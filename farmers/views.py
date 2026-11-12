import hashlib
import logging
import uuid

from django.conf import settings
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.db import DatabaseError, IntegrityError, transaction
from django.http import FileResponse, HttpResponse, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST
from django.contrib.admin.views.decorators import staff_member_required

from .forms import (
    BusinessReadinessForm,
    ConsultationLeadForm,
    FarmerDocumentFormSet,
    FarmerRegistrationForm,
    FinancialAnalysisDocumentFormSet,
    FinancialAnalysisRequestForm,
    NewsletterSubscriptionForm,
    RiskAssessmentDocumentFormSet,
    RiskAssessmentRequestForm,
    ResearcherApplicationForm,
    ResearchQuestionFormSet,
    ResearchResponseForm,
    ResearchStudyForm,
    MAX_DOCUMENT_SIZE,
    MAX_DOCUMENTS_PER_REGISTRATION,
    PartnerDocumentFormSet,
    PartnerRegistrationForm,
    sanitize_uploaded_image,
)
from .models import (
    FarmerDocument,
    FarmerProfile,
    FinancialAnalysisDocument,
    FinancialAnalysisRequest,
    PartnerDocument,
    PartnerProfile,
    RiskAssessmentDocument,
    RiskAssessmentRequest,
    ResearchInvitation,
    ResearchResponse,
    ResearchStudy,
    ResearcherApplication,
    NewsletterSubscription,
)


logger = logging.getLogger(__name__)
MAX_REGISTRATION_UPLOAD_SIZE = MAX_DOCUMENT_SIZE * MAX_DOCUMENTS_PER_REGISTRATION


def newsletter_signups_enabled():
    return (
        settings.DJANGO_ENVIRONMENT == "production"
        and settings.NEWSLETTER_SIGNUPS_ENABLED
        and not settings.DEMO_MODE
    )


@require_http_methods(["GET"])
def home(request):
    return render(
        request,
        "index.html",
        {
            "consultation_form": ConsultationLeadForm(),
            "newsletter_form": NewsletterSubscriptionForm(),
            "consultation_enabled": not settings.DEMO_MODE,
            "newsletter_enabled": newsletter_signups_enabled(),
        },
    )


@require_http_methods(["POST"])
def submit_consultation_lead(request):
    form = ConsultationLeadForm(request.POST)
    if _rate_limit_reached(request, "consultation"):
        form.add_error(None, "Too many requests. Please try again later.")
        return render(
            request,
            "index.html",
            {
                "consultation_form": form,
                "newsletter_form": NewsletterSubscriptionForm(),
                "consultation_enabled": not settings.DEMO_MODE,
                "newsletter_enabled": newsletter_signups_enabled(),
            },
            status=429,
        )

    if form.is_valid():
        lead = form.save(commit=False)
        now = timezone.now()
        lead.privacy_consent_at = now
        lead.last_contact_at = now
        lead.save()
        return redirect(
            "consultation_lead_received",
            reference=lead.public_reference,
        )

    return render(
        request,
        "index.html",
        {
            "consultation_form": form,
            "newsletter_form": NewsletterSubscriptionForm(),
            "consultation_enabled": not settings.DEMO_MODE,
            "newsletter_enabled": newsletter_signups_enabled(),
        },
        status=400,
    )


@require_http_methods(["POST"])
def subscribe_newsletter(request):
    if not newsletter_signups_enabled():
        return HttpResponseNotAllowed(
            ["GET"],
            "Newsletter signups are not currently available.",
        )

    form = NewsletterSubscriptionForm(request.POST)
    if _rate_limit_reached(request, "newsletter"):
        form.add_error(None, "Too many requests. Please try again later.")
        return render(
            request,
            "index.html",
            {
                "consultation_form": ConsultationLeadForm(),
                "newsletter_form": form,
                "consultation_enabled": not settings.DEMO_MODE,
                "newsletter_enabled": newsletter_signups_enabled(),
            },
            status=429,
        )

    if not form.is_valid():
        return render(
            request,
            "index.html",
            {
                "consultation_form": ConsultationLeadForm(),
                "newsletter_form": form,
                "consultation_enabled": not settings.DEMO_MODE,
                "newsletter_enabled": newsletter_signups_enabled(),
            },
            status=400,
        )

    email = form.cleaned_data["email"]
    try:
        subscription = NewsletterSubscription.objects.filter(email__iexact=email).first()
        now = timezone.now()
        if subscription is None:
            subscription = NewsletterSubscription.objects.create(
                email=email,
                topics=form.cleaned_data["topics"],
                consent_at=now,
            )
        else:
            resubscribing = subscription.status == NewsletterSubscription.Status.UNSUBSCRIBED
            subscription.topics = form.cleaned_data["topics"]
            subscription.status = NewsletterSubscription.Status.ACTIVE
            subscription.consent_at = now
            subscription.unsubscribed_at = None
            update_fields = ["topics", "status", "consent_at", "unsubscribed_at", "updated_at"]
            if resubscribing:
                subscription.unsubscribe_token = uuid.uuid4()
                update_fields.append("unsubscribe_token")
            subscription.save(update_fields=update_fields)
    except DatabaseError:
        logger.exception("Could not save MoFirms newsletter subscription.")
        form.add_error(None, "We couldn’t save your subscription. Please try again later.")
        return render(
            request,
            "index.html",
            {
                "consultation_form": ConsultationLeadForm(),
                "newsletter_form": form,
                "consultation_enabled": not settings.DEMO_MODE,
                "newsletter_enabled": newsletter_signups_enabled(),
            },
            status=503,
        )

    response = render(
        request,
        "farmers/newsletter_status.html",
        {
            "mode": "subscribed",
            "unsubscribe_url": reverse(
                "unsubscribe_newsletter",
                args=(subscription.unsubscribe_token,),
            ),
        },
    )
    response["Cache-Control"] = "no-store"
    response["Referrer-Policy"] = "no-referrer"
    return response


@require_http_methods(["GET", "POST"])
def unsubscribe_newsletter(request, token):
    subscription = get_object_or_404(
        NewsletterSubscription,
        unsubscribe_token=token,
        status=NewsletterSubscription.Status.ACTIVE,
    )
    if request.method == "POST":
        subscription.status = NewsletterSubscription.Status.UNSUBSCRIBED
        subscription.unsubscribed_at = timezone.now()
        subscription.save(update_fields=("status", "unsubscribed_at", "updated_at"))
        mode = "unsubscribed"
    else:
        mode = "confirm_unsubscribe"

    response = render(request, "farmers/newsletter_status.html", {"mode": mode})
    response["Cache-Control"] = "no-store"
    response["Referrer-Policy"] = "no-referrer"
    return response


def consultation_lead_received(request, reference):
    return render(
        request,
        "farmers/consultation_lead_success.html",
        {"reference": reference},
    )


def _client_rate_key(request, portal):
    address = request.META.get("REMOTE_ADDR", "unknown")
    digest = hashlib.sha256(address.encode("utf-8")).hexdigest()
    return f"{portal}-registration:{digest}"


def _rate_limit_reached(request, portal):
    key = _client_rate_key(request, portal)
    if cache.add(key, 1, settings.PORTAL_RATE_PERIOD):
        return False
    try:
        attempts = cache.incr(key)
    except ValueError:
        return not cache.add(key, 1, settings.PORTAL_RATE_PERIOD)
    return attempts > settings.PORTAL_RATE_LIMIT


@require_http_methods(["GET", "POST"])
def register_farmer(request):
    if request.method == "POST" and _rate_limit_reached(request, "farmer"):
        return render(
            request,
            "farmers/rate_limited.html",
            {"retry_after": settings.PORTAL_RATE_PERIOD // 60},
            status=429,
        )

    form = FarmerRegistrationForm(
        request.POST if request.method == "POST" else None,
        initial=(
            {"registration_type": FarmerProfile.RegistrationType.INDIVIDUAL}
            if request.method == "GET"
            else None
        ),
    )
    document_formset = FarmerDocumentFormSet(
        request.POST if request.method == "POST" else None,
        request.FILES if request.method == "POST" else None,
        prefix="documents",
    )
    upload_errors = []

    if request.method == "POST":
        is_valid = form.is_valid()
        documents_valid = document_formset.is_valid()
        uploads = []
        if documents_valid:
            for document_form in document_formset.forms:
                uploaded = document_form.cleaned_data.get("file")
                if uploaded:
                    uploads.append(uploaded)

        if sum(upload.size for upload in uploads) > MAX_REGISTRATION_UPLOAD_SIZE:
            upload_errors.append("The combined upload size must not exceed 100 MB.")
            documents_valid = False

        has_documents = bool(uploads)
        document_consent = request.POST.get("document_consent") == "on"
        if has_documents and not document_consent:
            upload_errors.append(
                "Please agree to the one-year document retention notice before uploading evidence.",
            )
            documents_valid = False

        if is_valid and documents_valid:
            new_account_user = None
            try:
                with transaction.atomic():
                    profile = form.save(commit=False)
                    now = timezone.now()
                    profile.privacy_consent_at = now
                    profile.last_contact_at = now
                    if form.cleaned_data["research_invite_consent"]:
                        profile.research_invite_consent_at = now
                    if has_documents:
                        profile.document_consent_at = now
                    profile.save()

                    for document_form in document_formset.forms:
                        cleaned = document_form.cleaned_data
                        uploaded = cleaned.get("file")
                        if not uploaded:
                            continue
                        document = FarmerDocument(
                            profile=profile,
                            document_type=cleaned["document_type"],
                            description=cleaned["description"],
                        )
                        safe_file = sanitize_uploaded_image(uploaded)
                        document.file.save(safe_file.name, safe_file, save=False)
                        document.save()

                    if form.cleaned_data.get("create_account"):
                        user_model = get_user_model()
                        email = form.cleaned_data["email"].strip().lower()
                        new_account_user = user_model(
                            username=email,
                            email=email,
                            first_name=profile.full_name[:150],
                        )
                        new_account_user.set_password(form.cleaned_data["password1"])
                        new_account_user.save()
                        profile.user = new_account_user
                        profile.save(update_fields=["user"])
            except (OSError, IntegrityError):
                logger.exception("Could not store a farmer registration upload.")
                form.add_error(
                    None,
                    "The registration could not be saved because a file could not be stored. Please try again.",
                )
            else:
                if new_account_user is not None:
                    login(request, new_account_user)
                    return redirect("farmer_dashboard")
                return redirect(
                    "registration_success",
                    reference=profile.public_reference,
                )

    return render(
        request,
        "farmers/register.html",
        {
            "form": form,
            "document_formset": document_formset,
            "max_documents": MAX_DOCUMENTS_PER_REGISTRATION,
            "max_file_size_mb": MAX_DOCUMENT_SIZE // (1024 * 1024),
            "max_total_size_mb": MAX_REGISTRATION_UPLOAD_SIZE // (1024 * 1024),
            "upload_errors": upload_errors,
        },
    )


def registration_success(request, reference):
    return render(
        request,
        "farmers/registration_success.html",
        {"reference": reference},
    )


@require_http_methods(["GET", "POST"])
def farmer_login(request):
    from django.contrib.auth.views import LoginView

    if request.method == "POST" and _rate_limit_reached(request, "farmer-login"):
        return render(
            request,
            "farmers/rate_limited.html",
            {"retry_after": settings.PORTAL_RATE_PERIOD // 60},
            status=429,
        )
    return LoginView.as_view(
        template_name="farmers/farmer_login.html",
        redirect_authenticated_user=True,
        next_page=reverse_lazy("farmer_dashboard"),
    )(request)


@require_POST
def farmer_logout(request):
    logout(request)
    return redirect("farmer_login")


@login_required(login_url="farmer_login")
def farmer_dashboard(request):
    profile = FarmerProfile.objects.filter(user=request.user).first()
    if profile is None:
        return render(request, "farmers/farmer_no_registration.html", status=404)
    documents = profile.documents.all()
    return render(
        request,
        "farmers/farmer_dashboard.html",
        {
            "profile": profile,
            "documents": documents,
        },
    )


@require_http_methods(["GET", "POST"])
def register_partner(request):
    if request.method == "POST" and _rate_limit_reached(request, "partner"):
        return render(
            request,
            "farmers/rate_limited.html",
            {"retry_after": settings.PORTAL_RATE_PERIOD // 60},
            status=429,
        )

    form = PartnerRegistrationForm(request.POST if request.method == "POST" else None)
    document_formset = PartnerDocumentFormSet(
        request.POST if request.method == "POST" else None,
        request.FILES if request.method == "POST" else None,
        prefix="documents",
    )
    upload_errors = []

    if request.method == "POST":
        is_valid = form.is_valid()
        documents_valid = document_formset.is_valid()
        uploads = []
        if documents_valid:
            for document_form in document_formset.forms:
                uploaded = document_form.cleaned_data.get("file")
                if uploaded:
                    uploads.append(uploaded)

        if sum(upload.size for upload in uploads) > MAX_REGISTRATION_UPLOAD_SIZE:
            upload_errors.append("The combined upload size must not exceed 100 MB.")
            documents_valid = False

        has_documents = bool(uploads)
        document_consent = request.POST.get("document_consent") == "on"
        if has_documents and not document_consent:
            upload_errors.append(
                "Please agree to the one-year document retention notice before uploading evidence."
            )
            documents_valid = False

        if is_valid and documents_valid:
            try:
                with transaction.atomic():
                    profile = form.save(commit=False)
                    now = timezone.now()
                    profile.contact_consent_at = now
                    if form.cleaned_data["listing_consent"]:
                        profile.listing_referral_consent_at = now
                    if form.cleaned_data["research_invite_consent"]:
                        profile.research_invite_consent_at = now
                    profile.last_contact_at = now
                    if has_documents:
                        profile.document_consent_at = now
                    profile.save()

                    for document_form in document_formset.forms:
                        cleaned = document_form.cleaned_data
                        uploaded = cleaned.get("file")
                        if not uploaded:
                            continue
                        document = PartnerDocument(
                            profile=profile,
                            document_type=cleaned["document_type"],
                            description=cleaned["description"],
                        )
                        safe_file = sanitize_uploaded_image(uploaded)
                        document.file.save(safe_file.name, safe_file, save=False)
                        document.save()
            except OSError:
                logger.exception("Could not store a partner registration upload.")
                form.add_error(
                    None,
                    "The registration could not be saved because a file could not be stored. Please try again.",
                )
            else:
                return redirect(
                    "partner_registration_success",
                    reference=profile.public_reference,
                )

    return render(
        request,
        "farmers/partner_register.html",
        {
            "form": form,
            "document_formset": document_formset,
            "max_documents": MAX_DOCUMENTS_PER_REGISTRATION,
            "max_file_size_mb": MAX_DOCUMENT_SIZE // (1024 * 1024),
            "max_total_size_mb": MAX_REGISTRATION_UPLOAD_SIZE // (1024 * 1024),
            "upload_errors": upload_errors,
        },
    )


def partner_registration_success(request, reference):
    return render(
        request,
        "farmers/partner_registration_success.html",
        {"reference": reference},
    )


@require_http_methods(["GET", "POST"])
def request_financial_analysis(request):
    return _submit_financial_analysis_request(
        request,
        form_class=FinancialAnalysisRequestForm,
        request_type=FinancialAnalysisRequest.RequestType.GENERAL,
        success_view="financial_analysis_success",
        template="farmers/financial_analysis_request.html",
        rate_key="financial-analysis",
    )


@require_http_methods(["GET", "POST"])
def request_business_readiness(request):
    return _submit_financial_analysis_request(
        request,
        form_class=BusinessReadinessForm,
        request_type=FinancialAnalysisRequest.RequestType.BUSINESS_READINESS,
        success_view="business_readiness_success",
        template="farmers/business_readiness_request.html",
        rate_key="business-readiness",
    )


def _submit_financial_analysis_request(
    request, *, form_class, request_type, success_view, template, rate_key
):
    if request.method == "POST" and _rate_limit_reached(request, rate_key):
        return render(
            request,
            "farmers/rate_limited.html",
            {"retry_after": settings.PORTAL_RATE_PERIOD // 60},
            status=429,
        )

    form = form_class(
        request.POST if request.method == "POST" else None
    )
    document_formset = FinancialAnalysisDocumentFormSet(
        request.POST if request.method == "POST" else None,
        request.FILES if request.method == "POST" else None,
        prefix="documents",
    )
    upload_errors = []

    if request.method == "POST":
        is_valid = form.is_valid()
        documents_valid = document_formset.is_valid()
        uploads = []
        if documents_valid:
            uploads = [
                document_form.cleaned_data["file"]
                for document_form in document_formset.forms
                if document_form.cleaned_data.get("file")
            ]

        if sum(upload.size for upload in uploads) > MAX_REGISTRATION_UPLOAD_SIZE:
            upload_errors.append("The combined upload size must not exceed 100 MB.")
            documents_valid = False

        has_documents = bool(uploads)
        if has_documents and request.POST.get("document_consent") != "on":
            upload_errors.append(
                "Please agree to the one-year document retention notice before uploading files."
            )
            documents_valid = False

        if is_valid and documents_valid:
            try:
                with transaction.atomic():
                    analysis_request = form.save(commit=False)
                    analysis_request.request_type = request_type
                    now = timezone.now()
                    analysis_request.contact_consent_at = now
                    analysis_request.last_contact_at = now
                    if has_documents:
                        analysis_request.document_consent_at = now
                    analysis_request.save()

                    for document_form in document_formset.forms:
                        cleaned = document_form.cleaned_data
                        uploaded = cleaned.get("file")
                        if not uploaded:
                            continue
                        document = FinancialAnalysisDocument(
                            request=analysis_request,
                            document_type=cleaned["document_type"],
                            description=cleaned["description"],
                        )
                        safe_file = sanitize_uploaded_image(uploaded)
                        document.file.save(safe_file.name, safe_file, save=False)
                        document.save()
            except OSError:
                logger.exception("Could not store a financial analysis upload.")
                form.add_error(
                    None,
                    "The request could not be saved because a file could not be stored. Please try again.",
                )
            else:
                return redirect(
                    success_view,
                    reference=analysis_request.public_reference,
                )

    return render(
        request,
        template,
        {
            "form": form,
            "document_formset": document_formset,
            "max_documents": MAX_DOCUMENTS_PER_REGISTRATION,
            "max_file_size_mb": MAX_DOCUMENT_SIZE // (1024 * 1024),
            "max_total_size_mb": MAX_REGISTRATION_UPLOAD_SIZE // (1024 * 1024),
            "upload_errors": upload_errors,
        },
    )


def financial_analysis_success(request, reference):
    return render(
        request,
        "farmers/financial_analysis_success.html",
        {"reference": reference},
    )


def business_readiness_success(request, reference):
    return render(
        request,
        "farmers/business_readiness_success.html",
        {"reference": reference},
    )


@require_http_methods(["GET", "POST"])
def request_risk_assessment(request):
    if request.method == "POST" and _rate_limit_reached(request, "risk-assessment"):
        return render(
            request,
            "farmers/rate_limited.html",
            {"retry_after": settings.PORTAL_RATE_PERIOD // 60},
            status=429,
        )

    form = RiskAssessmentRequestForm(request.POST if request.method == "POST" else None)
    document_formset = RiskAssessmentDocumentFormSet(
        request.POST if request.method == "POST" else None,
        request.FILES if request.method == "POST" else None,
        prefix="documents",
    )
    upload_errors = []

    if request.method == "POST":
        is_valid = form.is_valid()
        documents_valid = document_formset.is_valid()
        uploads = []
        if documents_valid:
            uploads = [
                document_form.cleaned_data["file"]
                for document_form in document_formset.forms
                if document_form.cleaned_data.get("file")
            ]

        if sum(upload.size for upload in uploads) > MAX_REGISTRATION_UPLOAD_SIZE:
            upload_errors.append("The combined upload size must not exceed 100 MB.")
            documents_valid = False

        has_documents = bool(uploads)
        if has_documents and request.POST.get("document_consent") != "on":
            upload_errors.append(
                "Please agree to the one-year document retention notice before uploading files."
            )
            documents_valid = False

        if is_valid and documents_valid:
            try:
                with transaction.atomic():
                    assessment_request = form.save(commit=False)
                    now = timezone.now()
                    assessment_request.contact_consent_at = now
                    assessment_request.last_contact_at = now
                    if has_documents:
                        assessment_request.document_consent_at = now
                    assessment_request.save()

                    for document_form in document_formset.forms:
                        cleaned = document_form.cleaned_data
                        uploaded = cleaned.get("file")
                        if not uploaded:
                            continue
                        document = RiskAssessmentDocument(
                            request=assessment_request,
                            document_type=cleaned["document_type"],
                            description=cleaned["description"],
                        )
                        safe_file = sanitize_uploaded_image(uploaded)
                        document.file.save(safe_file.name, safe_file, save=False)
                        document.save()
            except OSError:
                logger.exception("Could not store a risk assessment upload.")
                form.add_error(
                    None,
                    "The request could not be saved because a file could not be stored. Please try again.",
                )
            else:
                return redirect(
                    "risk_assessment_success",
                    reference=assessment_request.public_reference,
                )

    return render(
        request,
        "farmers/risk_assessment_request.html",
        {
            "form": form,
            "document_formset": document_formset,
            "max_documents": MAX_DOCUMENTS_PER_REGISTRATION,
            "max_file_size_mb": MAX_DOCUMENT_SIZE // (1024 * 1024),
            "max_total_size_mb": MAX_REGISTRATION_UPLOAD_SIZE // (1024 * 1024),
            "upload_errors": upload_errors,
        },
    )


def risk_assessment_success(request, reference):
    return render(
        request,
        "farmers/risk_assessment_success.html",
        {"reference": reference},
    )


def register_researcher(request):
    if request.method == "POST" and _rate_limit_reached(request, "researcher-application"):
        return render(
            request,
            "farmers/rate_limited.html",
            {"retry_after": settings.PORTAL_RATE_PERIOD // 60},
            status=429,
        )

    form = ResearcherApplicationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                user_model = get_user_model()
                email = form.cleaned_data["email"]
                user = user_model(
                    username=email,
                    email=email,
                    first_name=form.cleaned_data["organisation_name"][:150],
                    is_active=False,
                )
                user.set_password(form.cleaned_data["password1"])
                user.save()
                ResearcherApplication.objects.create(
                    user=user,
                    applicant_type=form.cleaned_data["applicant_type"],
                    organisation_name=form.cleaned_data["organisation_name"],
                    role_title=form.cleaned_data["role_title"],
                    phone=form.cleaned_data["phone"],
                    website=form.cleaned_data["website"],
                    country=form.cleaned_data["country"],
                    supervisor_name=form.cleaned_data["supervisor_name"],
                    supervisor_email=form.cleaned_data["supervisor_email"],
                    research_purpose=form.cleaned_data["research_purpose"],
                    methods_summary=form.cleaned_data["methods_summary"],
                    privacy_policy_url=form.cleaned_data["privacy_policy_url"],
                    data_protection_contact=form.cleaned_data["data_protection_contact"],
                    consent_at=timezone.now(),
                )
        except IntegrityError:
            logger.exception("Could not save a Portal E researcher application.")
            form.add_error(
                None,
                "The application could not be saved. Please try again or contact MoFirms.",
            )
        else:
            return redirect("researcher_application_received")

    return render(request, "farmers/researcher_register.html", {"form": form})


def researcher_application_received(request):
    return render(request, "farmers/researcher_application_received.html")


def _approved_researcher(request):
    if not request.user.is_authenticated:
        return None
    application = ResearcherApplication.objects.filter(user=request.user).first()
    if application and application.review_status == ResearcherApplication.ReviewStatus.APPROVED:
        return application
    return None


def researcher_login(request):
    from django.contrib.auth.views import LoginView

    if request.method == "POST" and _rate_limit_reached(request, "researcher-login"):
        return render(
            request,
            "farmers/rate_limited.html",
            {"retry_after": settings.PORTAL_RATE_PERIOD // 60},
            status=429,
        )
    return LoginView.as_view(
        template_name="farmers/researcher_login.html",
        redirect_authenticated_user=True,
    )(request)


@require_http_methods(["GET", "POST"])
def researcher_dashboard(request):
    if not request.user.is_authenticated:
        return redirect("researcher_login")
    researcher = _approved_researcher(request)
    if not researcher:
        return render(
            request,
            "farmers/researcher_access_pending.html",
            status=403,
        )

    if request.method == "POST" and request.POST.get("action") != "accept_quote":
        if _rate_limit_reached(request, "research-study"):
            return render(
                request,
                "farmers/rate_limited.html",
                {"retry_after": settings.PORTAL_RATE_PERIOD // 60},
                status=429,
            )

    form = ResearchStudyForm(request.POST or None)
    question_formset = ResearchQuestionFormSet(
        request.POST or None,
        prefix="questions",
    )
    if request.method == "POST":
        if request.POST.get("action") == "accept_quote":
            study = get_object_or_404(
                ResearchStudy,
                pk=request.POST.get("study_id"),
                researcher=researcher,
                status=ResearchStudy.Status.QUOTE_SENT,
                fee_quote_kes__isnull=False,
            )
            study.fee_accepted_at = timezone.now()
            study.status = ResearchStudy.Status.QUOTE_ACCEPTED
            study.save(update_fields=["fee_accepted_at", "status", "updated_at"])
            return redirect("researcher_dashboard")

        if form.is_valid() and question_formset.is_valid():
            try:
                with transaction.atomic():
                    study = form.save(commit=False)
                    study.researcher = researcher
                    study.status = ResearchStudy.Status.SUBMITTED
                    study.save()
                    position = 1
                    for question_form in question_formset.forms:
                        if not question_form.has_changed():
                            continue
                        question_form.save(study, position)
                        position += 1
            except IntegrityError:
                logger.exception("Could not save a Portal E study proposal.")
                form.add_error(
                    None,
                    "The study could not be submitted. Please review the information and try again.",
                )
            else:
                return redirect("researcher_dashboard")

    studies = list(researcher.studies.prefetch_related("questions"))
    for study in studies:
        responses = list(study.responses.all())
        study.response_count = len(responses)
        study.results_available = study.response_count >= 5
        study.result_questions = []
        if study.results_available:
            for question in study.questions.all():
                counts = {option: 0 for option in question.options}
                for response in responses:
                    answer = response.answers.get(str(question.pk), [])
                    if isinstance(answer, str):
                        answer = [answer]
                    for choice in answer:
                        if choice in counts:
                            counts[choice] += 1
                low_count = any(0 < count < 5 for count in counts.values())
                study.result_questions.append(
                    {
                        "prompt": question.prompt,
                        "withheld": low_count,
                        "counts": [] if low_count else list(counts.items()),
                    }
                )

    return render(
        request,
        "farmers/researcher_dashboard.html",
        {
            "researcher": researcher,
            "studies": studies,
            "form": form,
            "question_formset": question_formset,
        },
    )


def respond_to_research_invitation(request, token):
    if request.method == "POST" and _rate_limit_reached(
        request, f"research-response:{token}"
    ):
        return render(
            request,
            "farmers/rate_limited.html",
            {"retry_after": settings.PORTAL_RATE_PERIOD // 60},
            status=429,
        )

    invitation = get_object_or_404(
        ResearchInvitation.objects.select_related("study", "farmer_profile", "partner_profile"),
        token=token,
    )
    study = invitation.study
    now = timezone.now()
    unavailable = (
        invitation.completed_on is not None
        or invitation.expires_at <= now
        or study.status != ResearchStudy.Status.PUBLISHED
        or study.closes_at <= now
        or study.responses.count() >= study.target_sample_size
        or (
            invitation.farmer_profile
            and not invitation.farmer_profile.research_invite_consent_at
        )
        or (
            invitation.partner_profile
            and not invitation.partner_profile.research_invite_consent_at
        )
    )
    if unavailable:
        return render(request, "farmers/research_unavailable.html", status=410)

    questions = study.questions.all()
    form = ResearchResponseForm(
        request.POST or None,
        questions=questions,
    )
    if request.method == "POST":
        if form.is_valid():
            try:
                with transaction.atomic():
                    locked_invitation = ResearchInvitation.objects.select_for_update().select_related(
                        "study", "farmer_profile", "partner_profile"
                    ).get(pk=invitation.pk)
                    current_time = timezone.now()
                    if (
                        locked_invitation.completed_on is not None
                        or locked_invitation.expires_at <= current_time
                        or locked_invitation.study.status != ResearchStudy.Status.PUBLISHED
                        or locked_invitation.study.closes_at <= current_time
                        or locked_invitation.study.responses.count()
                        >= locked_invitation.study.target_sample_size
                        or (
                            locked_invitation.farmer_profile
                            and not locked_invitation.farmer_profile.research_invite_consent_at
                        )
                        or (
                            locked_invitation.partner_profile
                            and not locked_invitation.partner_profile.research_invite_consent_at
                        )
                    ):
                        return render(
                            request,
                            "farmers/research_unavailable.html",
                            status=410,
                        )
                    ResearchResponse.objects.create(
                        study=locked_invitation.study,
                        answers=form.response_answers(),
                        consented_on=timezone.localdate(current_time),
                        submitted_on=timezone.localdate(current_time),
                    )
                    locked_invitation.completed_on = timezone.localdate(current_time)
                    locked_invitation.farmer_profile = None
                    locked_invitation.partner_profile = None
                    locked_invitation.save(
                        update_fields=["completed_on", "farmer_profile", "partner_profile"]
                    )
            except ResearchInvitation.DoesNotExist:
                return render(request, "farmers/research_unavailable.html", status=410)
            except DatabaseError:
                logger.exception("Could not save an anonymous Portal E response.")
                form.add_error(
                    None,
                    "Your response could not be saved. Please try again.",
                )
            else:
                return render(request, "farmers/research_thanks.html")

    return render(
        request,
        "farmers/research_respond.html",
        {"study": study, "form": form},
    )


@staff_member_required
def download_document(request, document_id):
    document = get_object_or_404(FarmerDocument, pk=document_id)
    try:
        file_handle = document.file.open("rb")
    except FileNotFoundError:
        logger.exception("A stored farmer document is missing (document id %s).", document_id)
        return HttpResponse("The requested evidence file is unavailable.", status=404)

    response = FileResponse(
        file_handle,
        as_attachment=True,
        filename=f"{document.reference}.{document.file.name.rsplit('.', 1)[-1]}",
        content_type="application/octet-stream",
    )
    response["Cache-Control"] = "private, no-store"
    response["X-Content-Type-Options"] = "nosniff"
    response["Referrer-Policy"] = "no-referrer"
    return response


@staff_member_required
def download_partner_document(request, document_id):
    document = get_object_or_404(PartnerDocument, pk=document_id)
    try:
        file_handle = document.file.open("rb")
    except FileNotFoundError:
        logger.exception("A stored partner document is missing (document id %s).", document_id)
        return HttpResponse("The requested evidence file is unavailable.", status=404)

    response = FileResponse(
        file_handle,
        as_attachment=True,
        filename=f"{document.reference}.{document.file.name.rsplit('.', 1)[-1]}",
        content_type="application/octet-stream",
    )
    response["Cache-Control"] = "private, no-store"
    response["X-Content-Type-Options"] = "nosniff"
    response["Referrer-Policy"] = "no-referrer"
    return response


@staff_member_required
def download_financial_analysis_document(request, document_id):
    document = get_object_or_404(FinancialAnalysisDocument, pk=document_id)
    try:
        file_handle = document.file.open("rb")
    except FileNotFoundError:
        logger.exception(
            "A stored financial analysis document is missing (document id %s).",
            document_id,
        )
        return HttpResponse("The requested financial document is unavailable.", status=404)

    response = FileResponse(
        file_handle,
        as_attachment=True,
        filename=f"{document.reference}.{document.file.name.rsplit('.', 1)[-1]}",
        content_type="application/octet-stream",
    )
    response["Cache-Control"] = "private, no-store"
    response["X-Content-Type-Options"] = "nosniff"
    response["Referrer-Policy"] = "no-referrer"
    return response


@staff_member_required
def download_risk_assessment_document(request, document_id):
    document = get_object_or_404(RiskAssessmentDocument, pk=document_id)
    try:
        file_handle = document.file.open("rb")
    except FileNotFoundError:
        logger.exception(
            "A stored risk assessment document is missing (document id %s).",
            document_id,
        )
        return HttpResponse("The requested assessment document is unavailable.", status=404)

    response = FileResponse(
        file_handle,
        as_attachment=True,
        filename=f"{document.reference}.{document.file.name.rsplit('.', 1)[-1]}",
        content_type="application/octet-stream",
    )
    response["Cache-Control"] = "private, no-store"
    response["X-Content-Type-Options"] = "nosniff"
    response["Referrer-Policy"] = "no-referrer"
    return response
