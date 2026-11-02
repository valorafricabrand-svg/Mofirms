from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from farmers.models import (
    FarmerDocument,
    FarmerProfile,
    FinancialAnalysisDocument,
    FinancialAnalysisRequest,
    PartnerDocument,
    PartnerProfile,
)


class Command(BaseCommand):
    help = (
        "Preview or delete evidence older than 365 days and farmer, partner, or financial "
        "requests inactive for 730 days."
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
        expired_profiles = FarmerProfile.objects.filter(
            last_contact_at__lt=now - timedelta(days=730)
        )
        expired_partners = PartnerProfile.objects.filter(
            last_contact_at__lt=now - timedelta(days=730)
        )
        expired_analysis_requests = FinancialAnalysisRequest.objects.filter(
            last_contact_at__lt=now - timedelta(days=730)
        )
        document_count = (
            expired_documents.count()
            + expired_partner_documents.count()
            + expired_analysis_documents.count()
        )
        profile_count = (
            expired_profiles.count()
            + expired_partners.count()
            + expired_analysis_requests.count()
        )

        if not options["execute"]:
            self.stdout.write(
                self.style.WARNING(
                    f"Dry run: {document_count} document(s) and "
                    f"{profile_count} profile(s) are eligible for deletion. "
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

        self.stdout.write(
            self.style.SUCCESS(
                f"Deleted {deleted_documents} expired farmer/partner/financial document(s) and "
                f"{deleted_profiles} expired farmer/partner/financial request(s)."
            )
        )
