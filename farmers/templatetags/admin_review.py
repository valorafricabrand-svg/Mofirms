from django import template
from django.urls import reverse

from farmers.models import (
    ConsultationLead,
    FarmerDocument,
    FarmerProfile,
    FinancialAnalysisRequest,
    PartnerProfile,
    ResearcherApplication,
    ResearchStudy,
    RiskAssessmentRequest,
    WhatsAppContact,
)

register = template.Library()

REVIEW_QUEUES = (
    (FarmerProfile, "verification_status__exact", FarmerProfile.VerificationStatus.PENDING, None),
    (FarmerDocument, "review_status__exact", FarmerDocument.ReviewStatus.PENDING, None),
    (PartnerProfile, "verification_status__exact", PartnerProfile.ReviewStatus.PENDING, None),
    (ConsultationLead, "status__exact", ConsultationLead.Status.NEW, None),
    (WhatsAppContact, "help_requested_at__isnull", False, "WhatsApp callback requests"),
    (WhatsAppContact, "deletion_requested_at__isnull", False, "WhatsApp data deletion requests"),
    (FinancialAnalysisRequest, "status__exact", FinancialAnalysisRequest.ServiceStatus.PENDING, None),
    (RiskAssessmentRequest, "status__exact", RiskAssessmentRequest.ServiceStatus.PENDING, None),
    (ResearcherApplication, "review_status__exact", ResearcherApplication.ReviewStatus.PENDING, None),
    (ResearchStudy, "status__exact", ResearchStudy.Status.SUBMITTED, None),
)


def queue_url(model, lookup, value):
    opts = model._meta
    changelist = reverse(f"admin:{opts.app_label}_{opts.model_name}_changelist")
    return f"{changelist}?{lookup}={value}"


@register.simple_tag(takes_context=True)
def review_queue(context):
    user = context["request"].user
    queue = []
    for model, lookup, value, label in REVIEW_QUEUES:
        opts = model._meta
        if not (
            user.has_perm(f"{opts.app_label}.view_{opts.model_name}")
            or user.has_perm(f"{opts.app_label}.change_{opts.model_name}")
        ):
            continue
        queue.append(
            {
                "label": label or opts.verbose_name_plural.capitalize(),
                "count": model.objects.filter(**{lookup: value}).count(),
                "url": queue_url(model, lookup, value),
            }
        )
    return queue
