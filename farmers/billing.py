import json
import logging
from datetime import timedelta
from decimal import Decimal, InvalidOperation

from django import forms
from django.db import IntegrityError, transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST

from .models import BetaEnrollment, BetaInvite, MpesaPayment, ServicePlan
from .mpesa import (
    MpesaError,
    initiate_stk_push,
    mask_phone_number,
    normalize_phone_number,
    payments_available,
    query_stk_status,
)


logger = logging.getLogger(__name__)


class BetaConsentForm(forms.Form):
    consent = forms.BooleanField(
        required=True,
        label=(
            "I agree to the private beta terms and allow MoFirms to use my profile "
            "to administer this invitation."
        ),
    )


class PaymentForm(forms.Form):
    plan = forms.ModelChoiceField(queryset=ServicePlan.objects.none())
    phone_number = forms.CharField(max_length=32, label="M-PESA phone number")
    payment_consent = forms.BooleanField(
        required=True,
        label="I agree to pay the displayed package amount for the confirmed scope.",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["plan"].queryset = ServicePlan.objects.filter(active=True)

    def clean_phone_number(self):
        try:
            return normalize_phone_number(self.cleaned_data["phone_number"])
        except MpesaError as error:
            raise forms.ValidationError(str(error)) from error


def pricing(request):
    return render(
        request,
        "pricing.html",
        {"plans": ServicePlan.objects.filter(active=True)},
    )


def public_checkout(request):
    return render(
        request,
        "checkout.html",
        {"plans": ServicePlan.objects.filter(active=True)},
    )


@require_http_methods(["GET", "POST"])
def redeem_beta_invite(request, token):
    invite = get_object_or_404(BetaInvite, token=token)
    if (
        not invite.active
        or
        invite.redeemed_at
        or invite.expires_at <= timezone.now()
        or not invite.profile_is_verified
    ):
        return render(request, "farmers/beta_invite_unavailable.html", status=410)

    form = BetaConsentForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                locked_invite = BetaInvite.objects.select_for_update().get(pk=invite.pk)
                if (
                    not locked_invite.active
                    or
                    locked_invite.redeemed_at
                    or locked_invite.expires_at <= timezone.now()
                    or not locked_invite.profile_is_verified
                ):
                    return render(request, "farmers/beta_invite_unavailable.html", status=410)
                enrollment = BetaEnrollment.objects.create(
                    invite=locked_invite,
                    consent_at=timezone.now(),
                )
                locked_invite.redeemed_at = timezone.now()
                locked_invite.save(update_fields=["redeemed_at"])
        except IntegrityError:
            return render(request, "farmers/beta_invite_unavailable.html", status=410)
        return redirect("beta_enrollment", token=enrollment.access_token)

    return render(
        request,
        "farmers/beta_invite.html",
        {
            "form": form,
            "profile": invite.farmer_profile or invite.partner_profile,
        },
    )


@require_http_methods(["GET", "POST"])
def beta_enrollment(request, token):
    enrollment = get_object_or_404(
        BetaEnrollment.objects.select_related(
            "invite__farmer_profile", "invite__partner_profile"
        ),
        access_token=token,
    )
    if not enrollment.invite.active or not enrollment.invite.profile_is_verified:
        return render(request, "farmers/beta_invite_unavailable.html", status=410)
    if enrollment.status == BetaEnrollment.Status.APPROVED:
        return redirect("beta_checkout", token=enrollment.access_token)
    return render(
        request,
        "farmers/beta_enrollment.html",
        {"enrollment": enrollment},
    )


@require_http_methods(["GET", "POST"])
def beta_checkout(request, token):
    enrollment = get_object_or_404(
        BetaEnrollment.objects.select_related(
            "invite__farmer_profile", "invite__partner_profile"
        ),
        access_token=token,
    )
    if (
        enrollment.status != BetaEnrollment.Status.APPROVED
        or not enrollment.invite.active
        or not enrollment.invite.profile_is_verified
    ):
        return render(
            request,
            "farmers/beta_enrollment.html",
            {"enrollment": enrollment},
            status=403,
        )

    form = PaymentForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        plan = form.cleaned_data["plan"]
        phone_number = form.cleaned_data["phone_number"]
        try:
            with transaction.atomic():
                stale_payments = enrollment.payments.select_for_update().filter(
                    status__in=[MpesaPayment.Status.INITIATING, MpesaPayment.Status.PENDING],
                    created_at__lt=timezone.now() - timedelta(minutes=15),
                )
                for stale_payment in stale_payments:
                    stale_payment.status = MpesaPayment.Status.FAILED
                    stale_payment.phone_number = mask_phone_number(stale_payment.phone_number)
                    stale_payment.result_description = (
                        "Payment request expired; no confirmation was received."
                    )
                    stale_payment.save(
                        update_fields=[
                            "status",
                            "phone_number",
                            "result_description",
                            "updated_at",
                        ]
                    )
                if enrollment.payments.filter(
                    status__in=[MpesaPayment.Status.INITIATING, MpesaPayment.Status.PENDING]
                ).exists():
                    form.add_error(
                        None,
                        "A payment request is already in progress. Complete it or wait 15 minutes before retrying.",
                    )
                    payment = None
                else:
                    payment = MpesaPayment.objects.create(
                        enrollment=enrollment,
                        plan=plan,
                        amount=plan.price,
                        phone_number=phone_number,
                        status=MpesaPayment.Status.INITIATING,
                    )
        except IntegrityError:
            form.add_error(
                None,
                "A payment request was started at the same time. Refresh the page before trying again.",
            )
            payment = None

        if payment is not None:
            try:
                response = initiate_stk_push(
                    phone_number=phone_number,
                    amount=plan.price,
                    account_reference=f"MF{payment.pk}",
                    description=plan.name,
                )
            except MpesaError as error:
                payment.status = MpesaPayment.Status.FAILED
                payment.phone_number = mask_phone_number(payment.phone_number)
                payment.result_description = str(error)[:255]
                payment.save(
                    update_fields=[
                        "status",
                        "phone_number",
                        "result_description",
                        "updated_at",
                    ]
                )
                form.add_error(None, str(error))
                logger.warning("M-PESA STK request failed for payment id %s: %s", payment.pk, error)
            else:
                payment.checkout_request_id = response["checkout_request_id"]
                payment.merchant_request_id = response["merchant_request_id"]
                payment.status = MpesaPayment.Status.PENDING
                payment.save(
                    update_fields=[
                        "checkout_request_id",
                        "merchant_request_id",
                        "status",
                        "updated_at",
                    ]
                )
                return redirect("payment_status", token=enrollment.access_token)

    return render(
        request,
        "farmers/beta_checkout.html",
        {
            "enrollment": enrollment,
            "form": form,
            "plans": ServicePlan.objects.filter(active=True),
            "payments": enrollment.payments.select_related("plan")[:5],
            "mpesa_ready": payments_available(),
        },
    )


@require_http_methods(["GET"])
def payment_status(request, token):
    enrollment = get_object_or_404(
        BetaEnrollment.objects.select_related(
            "invite__farmer_profile", "invite__partner_profile"
        ),
        access_token=token,
    )
    if not enrollment.invite.active or not enrollment.invite.profile_is_verified:
        return render(request, "farmers/beta_invite_unavailable.html", status=410)
    return render(
        request,
        "farmers/payment_status.html",
        {
            "enrollment": enrollment,
            "payments": enrollment.payments.select_related("plan")[:10],
        },
    )


def _callback_metadata(callback):
    callback_metadata = callback.get("CallbackMetadata")
    if not isinstance(callback_metadata, dict):
        return {}
    metadata = callback_metadata.get("Item", [])
    if not isinstance(metadata, list):
        return {}
    return {
        item.get("Name"): item.get("Value")
        for item in metadata
        if isinstance(item, dict) and isinstance(item.get("Name"), str)
    }


@csrf_exempt
@require_POST
def mpesa_callback(request):
    if len(request.body) > 65536:
        return HttpResponse(status=413)
    try:
        payload = json.loads(request.body)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return JsonResponse({"ResultCode": 1, "ResultDesc": "Invalid callback body."}, status=400)
    body = payload.get("Body") if isinstance(payload, dict) else None
    callback = body.get("stkCallback") if isinstance(body, dict) else None
    if not isinstance(callback, dict):
        return JsonResponse({"ResultCode": 1, "ResultDesc": "Invalid callback structure."}, status=400)

    checkout_request_id = callback.get("CheckoutRequestID")
    if not isinstance(checkout_request_id, str) or not checkout_request_id:
        return JsonResponse({"ResultCode": 1, "ResultDesc": "Missing request identifier."}, status=400)
    payment = MpesaPayment.objects.filter(
        checkout_request_id=checkout_request_id,
        status=MpesaPayment.Status.PENDING,
    ).first()
    if payment is None:
        return JsonResponse({"ResultCode": 0, "ResultDesc": "Callback recorded."})

    try:
        query = query_stk_status(checkout_request_id)
    except MpesaError as error:
        logger.warning("Could not verify M-PESA callback for payment id %s: %s", payment.pk, error)
        return JsonResponse(
            {"ResultCode": 1, "ResultDesc": "Payment verification is temporarily unavailable."},
            status=503,
        )

    query_code = str(query.get("ResultCode", ""))
    if not query_code:
        logger.warning("M-PESA query returned no result code for payment id %s.", payment.pk)
        return JsonResponse(
            {"ResultCode": 1, "ResultDesc": "Payment verification is temporarily unavailable."},
            status=503,
        )
    callback_code = str(callback.get("ResultCode", ""))
    if query_code != "0":
        with transaction.atomic():
            locked_payment = MpesaPayment.objects.select_for_update().get(pk=payment.pk)
            if locked_payment.status == MpesaPayment.Status.PENDING:
                locked_payment.status = MpesaPayment.Status.FAILED
                locked_payment.phone_number = mask_phone_number(locked_payment.phone_number)
                locked_payment.result_code = query_code[:24]
                locked_payment.result_description = str(
                    query.get("ResultDesc") or callback.get("ResultDesc") or "M-PESA payment was not completed."
                )[:255]
                locked_payment.save(
                    update_fields=[
                        "status",
                        "phone_number",
                        "result_code",
                        "result_description",
                        "updated_at",
                    ]
                )
        return JsonResponse({"ResultCode": 0, "ResultDesc": "Callback processed."})

    metadata = _callback_metadata(callback)
    receipt = metadata.get("MpesaReceiptNumber")
    callback_amount = metadata.get("Amount")
    callback_phone = metadata.get("PhoneNumber")
    callback_merchant_id = callback.get("MerchantRequestID")
    try:
        amount_matches = (
            callback_amount is not None
            and Decimal(str(callback_amount)) == payment.amount
        )
    except (InvalidOperation, TypeError, ValueError):
        amount_matches = False
    if (
        callback_code != "0"
        or not receipt
        or not amount_matches
        or str(callback_phone or "") != payment.phone_number
        or (
            callback_merchant_id
            and callback_merchant_id != payment.merchant_request_id
        )
    ):
        logger.warning("M-PESA callback details did not match payment id %s.", payment.pk)
        return JsonResponse({"ResultCode": 0, "ResultDesc": "Callback recorded."})

    try:
        with transaction.atomic():
            locked_payment = MpesaPayment.objects.select_for_update().get(pk=payment.pk)
            if locked_payment.status == MpesaPayment.Status.PENDING:
                locked_payment.status = MpesaPayment.Status.PAID
                locked_payment.phone_number = mask_phone_number(locked_payment.phone_number)
                locked_payment.mpesa_receipt = str(receipt)[:32]
                locked_payment.result_code = "0"
                locked_payment.result_description = "Payment confirmed by M-PESA."
                locked_payment.paid_at = timezone.now()
                locked_payment.save(
                    update_fields=[
                        "status",
                        "phone_number",
                        "mpesa_receipt",
                        "result_code",
                        "result_description",
                        "paid_at",
                        "updated_at",
                    ]
                )
    except IntegrityError:
        logger.exception("Duplicate M-PESA receipt received for payment id %s.", payment.pk)
        return JsonResponse(
            {"ResultCode": 1, "ResultDesc": "Duplicate transaction receipt."},
            status=409,
        )
    return JsonResponse({"ResultCode": 0, "ResultDesc": "Callback processed."})
