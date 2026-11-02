import hashlib
import logging
from datetime import datetime
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.db import IntegrityError, transaction
from django.db.models import Count, Q, Sum
from django.db.models.functions import Coalesce
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST

from .forms import (
    CreditSettlementForm,
    FarmerSignupForm,
    FarmEnterpriseForm,
    LedgerEntryForm,
)
from .models import CreditSettlement, FarmEnterprise, LedgerEntry


logger = logging.getLogger(__name__)


def _rate_limit_reached(request, key):
    address = request.META.get("REMOTE_ADDR", "unknown")
    address_hash = hashlib.sha256(address.encode("utf-8")).hexdigest()
    cache_key = f"smart-hasibu:{key}:{address_hash}"
    if cache.add(cache_key, 1, 60 * 60):
        return False
    try:
        return cache.incr(cache_key) > 5
    except ValueError:
        return not cache.add(cache_key, 1, 60 * 60)


def _month_bounds(month_value):
    try:
        selected = datetime.strptime(month_value, "%Y-%m").date().replace(day=1)
    except (TypeError, ValueError):
        return None
    if selected.strftime("%Y-%m") != month_value:
        return None
    if selected.month == 12:
        next_month = selected.replace(year=selected.year + 1, month=1)
    else:
        next_month = selected.replace(month=selected.month + 1)
    return selected, next_month


@require_http_methods(["GET", "POST"])
def signup(request):
    if request.user.is_authenticated:
        return redirect("smart_hasibu:dashboard")
    if request.method == "POST" and _rate_limit_reached(request, "signup"):
        return render(
            request,
            "smart_hasibu/signup.html",
            {"form": FarmerSignupForm(request.POST), "rate_limited": True},
            status=429,
        )

    form = FarmerSignupForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                user = form.save()
        except IntegrityError:
            logger.exception("Could not create a SmartHasibu farmer account.")
            form.add_error(None, "The account could not be created. Please try again.")
        else:
            login(request, user)
            return redirect("smart_hasibu:dashboard")
    return render(request, "smart_hasibu/signup.html", {"form": form})


@require_http_methods(["GET", "POST"])
def signin(request):
    if request.user.is_authenticated:
        return redirect("smart_hasibu:dashboard")
    if request.method == "POST" and _rate_limit_reached(request, "login"):
        return render(
            request,
            "smart_hasibu/login.html",
            {"rate_limited": True, "email": request.POST.get("email", "")},
            status=429,
        )
    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")
        user_model = get_user_model()
        user_record = user_model.objects.filter(email__iexact=email).only("username").first()
        user = authenticate(
            request,
            username=user_record.username if user_record else email,
            password=password,
        )
        if user is not None:
            login(request, user)
            return redirect("smart_hasibu:dashboard")
        messages.error(request, "Sign-in failed. Check your email and password.")
    return render(request, "smart_hasibu/login.html", {"email": request.POST.get("email", "")})


@require_POST
def signout(request):
    logout(request)
    return redirect("smart_hasibu:login")


@login_required(login_url="smart_hasibu:login")
@require_http_methods(["GET", "POST"])
def dashboard(request):
    month_value = request.GET.get("month", timezone.localdate().strftime("%Y-%m"))
    bounds = _month_bounds(month_value)
    if not bounds:
        return HttpResponseBadRequest("Choose a valid month in YYYY-MM format.")
    start_date, end_date = bounds
    entries = LedgerEntry.objects.filter(
        enterprise__owner=request.user,
        occurred_on__gte=start_date,
        occurred_on__lt=end_date,
    ).select_related("enterprise")
    enterprise_value = request.GET.get("enterprise", "")
    selected_enterprise = None
    if enterprise_value:
        try:
            enterprise_id = int(enterprise_value)
        except (TypeError, ValueError):
            return HttpResponseBadRequest("Choose a valid enterprise.")
        selected_enterprise = get_object_or_404(
            FarmEnterprise,
            pk=enterprise_id,
            owner=request.user,
        )
        entries = entries.filter(enterprise=selected_enterprise)

    summary = entries.aggregate(
        income=Coalesce(
            Sum("amount", filter=Q(entry_type=LedgerEntry.EntryType.INCOME)),
            Decimal("0.00"),
        ),
        expenses=Coalesce(
            Sum("amount", filter=Q(entry_type=LedgerEntry.EntryType.EXPENSE)),
            Decimal("0.00"),
        ),
        count=Count("pk"),
    )
    display_entries = entries.annotate(
        settled=Coalesce(Sum("settlements__amount"), Decimal("0.00"))
    )
    credit_entries = LedgerEntry.objects.filter(
        enterprise__owner=request.user,
        is_credit=True,
    )
    if selected_enterprise:
        credit_entries = credit_entries.filter(enterprise=selected_enterprise)
    credit_entries = credit_entries.annotate(
        settled=Coalesce(Sum("settlements__amount"), Decimal("0.00"))
    )
    balances = {
        LedgerEntry.EntryType.INCOME: Decimal("0.00"),
        LedgerEntry.EntryType.EXPENSE: Decimal("0.00"),
    }
    for credit_entry in credit_entries:
        balances[credit_entry.entry_type] += max(
            credit_entry.amount - credit_entry.settled,
            Decimal("0.00"),
        )

    enterprise_form = FarmEnterpriseForm()
    entry_form = LedgerEntryForm(user=request.user)
    settlement_form = CreditSettlementForm(user=request.user)
    if request.method == "POST":
        if request.POST.get("action") == "enterprise":
            enterprise_form = FarmEnterpriseForm(request.POST)
            if enterprise_form.is_valid():
                enterprise = enterprise_form.save(commit=False)
                enterprise.owner = request.user
                try:
                    with transaction.atomic():
                        enterprise.save()
                except IntegrityError:
                    enterprise_form.add_error(
                        "name",
                        "You already have an enterprise with this name.",
                    )
                else:
                    messages.success(request, "Enterprise added.")
                    return redirect("smart_hasibu:dashboard")
        elif request.POST.get("action") == "entry":
            entry_form = LedgerEntryForm(request.POST, user=request.user)
            if entry_form.is_valid():
                entry_form.save()
                messages.success(request, "Record saved to your private cashbook.")
                return redirect("smart_hasibu:dashboard")
        elif request.POST.get("action") == "settlement":
            settlement_form = CreditSettlementForm(request.POST, user=request.user)
            if settlement_form.is_valid():
                try:
                    with transaction.atomic():
                        credit_entry = LedgerEntry.objects.select_for_update().get(
                            pk=settlement_form.cleaned_data["entry"].pk,
                            enterprise__owner=request.user,
                            is_credit=True,
                        )
                        prior_settlements = credit_entry.settlements.aggregate(
                            total=Coalesce(Sum("amount"), Decimal("0.00"))
                        )["total"]
                        payment = settlement_form.save(commit=False)
                        if prior_settlements + payment.amount > credit_entry.amount:
                            settlement_form.add_error(
                                "amount",
                                "The payment is greater than the outstanding balance.",
                            )
                        else:
                            payment.entry = credit_entry
                            payment.save()
                            messages.success(request, "Credit payment recorded.")
                            return redirect("smart_hasibu:dashboard")
                except LedgerEntry.DoesNotExist:
                    settlement_form.add_error(
                        "entry",
                        "Select an outstanding credit record from your account.",
                    )
        else:
            return HttpResponseBadRequest("Choose a valid cashbook action.")

    return render(
        request,
        "smart_hasibu/dashboard.html",
        {
            "month": month_value,
            "entries": display_entries[:100],
            "enterprises": FarmEnterprise.objects.filter(owner=request.user),
            "selected_enterprise": selected_enterprise,
            "income_total": summary["income"],
            "expense_total": summary["expenses"],
            "net_total": summary["income"] - summary["expenses"],
            "entry_count": summary["count"],
            "receivable_total": balances[LedgerEntry.EntryType.INCOME],
            "payable_total": balances[LedgerEntry.EntryType.EXPENSE],
            "enterprise_form": enterprise_form,
            "entry_form": entry_form,
            "settlement_form": settlement_form,
        },
    )
