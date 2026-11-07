from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone

from farmers.models import (
    ConsultationLead,
    FarmerDocument,
    FarmerProfile,
    FinancialAnalysisDocument,
    FinancialAnalysisRequest,
    PartnerDocument,
    PartnerProfile,
    ResearchInvitation,
    ResearchResponse,
    ResearcherApplication,
    ResearchStudy,
    RiskAssessmentDocument,
    RiskAssessmentRequest,
)


class Command(BaseCommand):
    help = (
        "Preview or delete evidence and research data older than 365 days, plus farmer, "
        "partner, financial, consultation, or researcher records inactive for 730 days."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--execute",
            action="store_true",
            help="Delete expired database records and their private evidence files.",
        )

    def handle(self, *args, **options):
        now = timezone.now()
        expired_documents = FarmerDocument.objects.filter(
            uploaded_at__lt=now - timedelta(days=365)
        )
        expired_partner_documents = PartnerDocument.objects.filter(
            uploaded_at__lt=now - timedelta(days=365)
        )
        expired_analysis_documents = FinancialAnalysisDocument.objects.filter(
            uploaded_at__lt=now - timedelta(days=365)
        )
        expired_risk_documents = RiskAssessmentDocument.objects.filter(
            uploaded_at__lt=now - timedelta(days=365)
        )
        expired_profiles = FarmerProfile.objects.filter(
            last_contact_at__lt=now - timedelta(days=730)
        )
        expired_partners = PartnerProfile.objects.filter(
            last_contact_at__lt=now - timedelta(days=730)
        )
        expired_analysis_requests = FinancialAnalysisRequest.objects.filter(
            last_contact_at__lt=now - timedelta(days=730)
        )
        expired_risk_requests = RiskAssessmentRequest.objects.filter(
            last_contact_at__lt=now - timedelta(days=730)
        )
        expired_consultation_leads = ConsultationLead.objects.filter(
            last_contact_at__lt=now - timedelta(days=730)
        )
        expired_researchers = ResearcherApplication.objects.filter(
            last_contact_at__lt=now - timedelta(days=730)
        )
        expired_research_studies = ResearchStudy.objects.filter(
            researcher__in=expired_researchers
        )
        expired_research_responses = ResearchResponse.objects.filter(
            Q(submitted_on__lt=now.date() - timedelta(days=365))
            | Q(study__in=expired_research_studies)
        ).distinct()
        expired_research_invitations = ResearchInvitation.objects.filter(
            Q(expires_at__lt=now)
            | Q(study__in=expired_research_studies)
            | Q(farmer_profile__in=expired_profiles)
            | Q(partner_profile__in=expired_partners)
        ).distinct()
        document_count = (
            expired_documents.count()
            + expired_partner_documents.count()
            + expired_analysis_documents.count()
            + expired_risk_documents.count()
        )
        profile_count = (
            expired_profiles.count()
            + expired_partners.count()
            + expired_analysis_requests.count()
            + expired_risk_requests.count()
            + expired_researchers.count()
        )
        consultation_lead_count = expired_consultation_leads.count()
        response_count = expired_research_responses.count()
        invitation_count = expired_research_invitations.count()
        study_count = expired_research_studies.count()

        if not options["execute"]:
            self.stdout.write(
                self.style.WARNING(
                    f"Dry run: {document_count} document(s) and "
                    f"{profile_count} profile/request(s), {consultation_lead_count} "
                    f"consultation enquiry/enquiries, {study_count} research study/studies, "
                    f"{response_count} research response(s), and {invitation_count} "
                    f"invitation(s) are eligible "
                    "for deletion. "
                    "Add --execute to delete them."
                )
            )
            return

        deleted_documents = 0
        for document in expired_documents.iterator():
            document.delete()
            deleted_documents += 1
        for document in expired_partner_documents.iterator():
            document.delete()
            deleted_documents += 1
        for document in expired_analysis_documents.iterator():
            document.delete()
            deleted_documents += 1
        for document in expired_risk_documents.iterator():
            document.delete()
            deleted_documents += 1

        deleted_research_responses, _ = expired_research_responses.delete()
        deleted_research_invitations, _ = expired_research_invitations.delete()
        expired_research_studies.delete()
        deleted_research_studies = study_count

        deleted_profiles = 0
        for profile in expired_profiles.iterator():
            profile.delete()
            deleted_profiles += 1
        for profile in expired_partners.iterator():
            profile.delete()
            deleted_profiles += 1
        for analysis_request in expired_analysis_requests.iterator():
            analysis_request.delete()
            deleted_profiles += 1
        for risk_request in expired_risk_requests.iterator():
            risk_request.delete()
            deleted_profiles += 1
        deleted_consultation_leads, _ = expired_consultation_leads.delete()
        for researcher in expired_researchers.select_related("user").iterator():
            researcher.user.delete()
            deleted_profiles += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Deleted {deleted_documents} expired farmer/partner/financial document(s) and "
                f"{deleted_profiles} expired farmer/partner/financial/research record(s), "
                f"{deleted_consultation_leads} expired consultation enquiry/enquiries, "
                f"{deleted_research_studies} research study record(s), "
                f"{deleted_research_responses} research response record(s), and "
                f"{deleted_research_invitations} invitation record(s)."
            )
        )
