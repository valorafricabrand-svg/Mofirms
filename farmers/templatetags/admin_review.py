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
)

register = template.Library()

REVIEW_QUEUES = (
    (FarmerProfile, "verification_status", FarmerProfile.VerificationStatus.PENDING),
    (FarmerDocument, "review_status", FarmerDocument.ReviewStatus.PENDING),
    (PartnerProfile, "verification_status", PartnerProfile.ReviewStatus.PENDING),
    (ConsultationLead, "status", ConsultationLead.Status.NEW),
    (FinancialAnalysisRequest, "status", FinancialAnalysisRequest.ServiceStatus.PENDING),
    (RiskAssessmentRequest, "status", RiskAssessmentRequest.ServiceStatus.PENDING),
    (ResearcherApplication, "review_status", ResearcherApplication.ReviewStatus.PENDING),
    (ResearchStudy, "status", ResearchStudy.Status.SUBMITTED),
)


@register.simple_tag(takes_context=True)
def review_queue(context):
    user = context["request"].user
    queue = []
    for model, field, value in REVIEW_QUEUES:
        opts = model._meta
        if not (
            user.has_perm(f"{opts.app_label}.view_{opts.model_name}")
            or user.has_perm(f"{opts.app_label}.change_{opts.model_name}")
        ):
            continue
        changelist = reverse(f"admin:{opts.app_label}_{opts.model_name}_changelist")
        queue.append(
            {
                "label": opts.verbose_name_plural.capitalize(),
                "count": model.objects.filter(**{field: value}).count(),
                "url": f"{changelist}?{field}__exact={value}",
            }
        )
    return queue
