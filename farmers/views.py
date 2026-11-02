import hashlib
import logging

from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.http import FileResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.contrib.admin.views.decorators import staff_member_required

from .forms import (
    FarmerDocumentFormSet,
    FarmerRegistrationForm,
    FinancialAnalysisDocumentFormSet,
    FinancialAnalysisRequestForm,
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
)


logger = logging.getLogger(__name__)
MAX_REGISTRATION_UPLOAD_SIZE = MAX_DOCUMENT_SIZE * MAX_DOCUMENTS_PER_REGISTRATION


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
            try:
                with transaction.atomic():
                    profile = form.save(commit=False)
                    now = timezone.now()
                    profile.privacy_consent_at = now
                    profile.last_contact_at = now
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
            except OSError:
                logger.exception("Could not store a farmer registration upload.")
                form.add_error(
                    None,
                    "The registration could not be saved because a file could not be stored. Please try again.",
                )
            else:
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
    if request.method == "POST" and _rate_limit_reached(request, "financial-analysis"):
        return render(
            request,
            "farmers/rate_limited.html",
            {"retry_after": settings.PORTAL_RATE_PERIOD // 60},
            status=429,
        )

    form = FinancialAnalysisRequestForm(
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
                    "financial_analysis_success",
                    reference=analysis_request.public_reference,
                )

    return render(
        request,
        "farmers/financial_analysis_request.html",
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
