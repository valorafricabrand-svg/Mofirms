from datetime import timedelta
from io import BytesIO, StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image, PngImagePlugin

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
    ResearchQuestion,
    ResearchResponse,
    ResearchStudy,
    ResearcherApplication,
)


def png_upload(name="proof.png", metadata=None):
    buffer = BytesIO()
    image = Image.new("RGB", (20, 20), color="green")
    image.save(buffer, format="PNG", pnginfo=metadata)
    return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/png")


class FarmerRegistrationTests(TestCase):
    def setUp(self):
        cache.clear()
        self.private_files = TemporaryDirectory()
        self.addCleanup(self.private_files.cleanup)
        self.settings_override = override_settings(
            MEDIA_ROOT=self.private_files.name,
            PRIVATE_UPLOAD_ROOT=self.private_files.name,
            ANTIVIRUS_ENABLED=False,
        )
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)
        self.url = reverse("register_farmer")
        self.individual_data = {
            "registration_type": "individual",
            "full_name": "Sample Farmer",
            "phone": "0712345678",
            "preferred_contact": "phone",
            "county": "Vihiga",
            "privacy_consent": "on",
            "documents-TOTAL_FORMS": "0",
            "documents-INITIAL_FORMS": "0",
            "documents-MIN_NUM_FORMS": "0",
            "documents-MAX_NUM_FORMS": "20",
        }

    def test_individual_registration_is_saved_for_manual_review(self):
        response = self.client.post(self.url, self.individual_data)

        self.assertEqual(response.status_code, 302)
        self.assertRegex(response.url, r"^/portal/registered/[A-F0-9]{8}/$")
        profile = FarmerProfile.objects.get()
        self.assertEqual(profile.full_name, "Sample Farmer")
        self.assertEqual(profile.verification_status, FarmerProfile.VerificationStatus.PENDING)
        self.assertEqual(profile.identity_review_status, FarmerProfile.EvidenceStatus.PENDING)
        self.assertEqual(profile.farm_review_status, FarmerProfile.EvidenceStatus.PENDING)
        self.assertEqual(profile.group_review_status, FarmerProfile.EvidenceStatus.NOT_APPLICABLE)
        self.assertIsNotNone(profile.privacy_consent_at)
        self.assertIsNone(profile.research_invite_consent_at)

    def test_farmer_can_separately_opt_in_to_research_invitations(self):
        response = self.client.post(
            self.url,
            {**self.individual_data, "research_invite_consent": "on"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertIsNotNone(FarmerProfile.objects.get().research_invite_consent_at)

    def test_group_requires_details_and_authorisation(self):
        data = {
            **self.individual_data,
            "registration_type": "group",
            "group_name": "Sample Growers",
        }
        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(FarmerProfile.objects.count(), 0)
        self.assertContains(response, "This field is required for a group registration.")
        self.assertContains(response, "Confirm that you are authorised to register this group.")

        data.update(
            {
                "group_type": "farmer_group",
                "group_authorization_confirmed": "on",
                "group_registration_status": "registered",
                "group_registration_number": "FG-123",
            }
        )
        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, 302)
        profile = FarmerProfile.objects.get()
        self.assertEqual(profile.group_review_status, FarmerProfile.EvidenceStatus.PENDING)
        self.assertTrue(profile.group_authorization_confirmed)

    def test_document_upload_requires_explicit_consent_and_is_private(self):
        metadata = PngImagePlugin.PngInfo()
        metadata.add_text("Comment", "synthetic-private-metadata")
        upload = png_upload(metadata=metadata)
        data = {
            **self.individual_data,
            "documents-TOTAL_FORMS": "1",
            "documents-INITIAL_FORMS": "0",
            "documents-MIN_NUM_FORMS": "0",
            "documents-MAX_NUM_FORMS": "20",
            "documents-0-document_type": "identity",
            "documents-0-description": "Synthetic identity test",
            "documents-0-file": upload,
        }

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(FarmerProfile.objects.count(), 0)
        self.assertContains(response, "Please agree to the one-year document retention notice")

        upload = png_upload(metadata=metadata)
        data["documents-0-file"] = upload
        data["document_consent"] = "on"
        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, 302)
        profile = FarmerProfile.objects.get()
        document = FarmerDocument.objects.get(profile=profile)
        self.assertEqual(document.document_type, FarmerDocument.DocumentType.IDENTITY)
        self.assertIsNotNone(profile.document_consent_at)
        with document.file.open("rb") as stored:
            self.assertNotIn(b"synthetic-private-metadata", stored.read())
        self.assertEqual(self.client.get(document.file.url).status_code, 404)

    def test_upload_rejects_mismatched_file_content(self):
        fake_image = SimpleUploadedFile(
            "proof.png", b"%PDF-1.7 fake pdf", content_type="image/png"
        )
        data = {
            **self.individual_data,
            "documents-TOTAL_FORMS": "1",
            "documents-INITIAL_FORMS": "0",
            "documents-MIN_NUM_FORMS": "0",
            "documents-MAX_NUM_FORMS": "20",
            "documents-0-document_type": "identity",
            "documents-0-description": "",
            "documents-0-file": fake_image,
            "document_consent": "on",
        }

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(FarmerProfile.objects.count(), 0)
        self.assertContains(response, "file contents do not match")

    def test_registration_rejects_more_than_twenty_documents(self):
        data = {
            **self.individual_data,
            "documents-TOTAL_FORMS": "21",
            "documents-INITIAL_FORMS": "0",
            "documents-MIN_NUM_FORMS": "0",
            "documents-MAX_NUM_FORMS": "20",
        }

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(FarmerProfile.objects.count(), 0)
        self.assertContains(response, "Please submit at most 20 forms.")

    def test_verified_status_requires_a_recorded_basis(self):
        profile = FarmerProfile(
            registration_type=FarmerProfile.RegistrationType.INDIVIDUAL,
            full_name="Sample Farmer",
            preferred_contact=FarmerProfile.ContactPreference.PHONE,
            county="Vihiga",
            privacy_consent_at=timezone.now(),
            verification_status=FarmerProfile.VerificationStatus.VERIFIED,
        )

        with self.assertRaises(ValidationError) as error:
            profile.full_clean()
        self.assertIn("verification_notes", error.exception.message_dict)

        profile.verification_notes = "Contact details checked with the named farmer."
        profile.full_clean()

    def test_private_document_download_requires_staff(self):
        profile = FarmerProfile.objects.create(
            registration_type=FarmerProfile.RegistrationType.INDIVIDUAL,
            full_name="Sample Farmer",
            preferred_contact=FarmerProfile.ContactPreference.PHONE,
            county="Vihiga",
            privacy_consent_at=timezone.now(),
        )
        document = FarmerDocument.objects.create(
            profile=profile,
            document_type=FarmerDocument.DocumentType.FARM,
        )
        document.file.save("evidence.png", png_upload(), save=True)
        url = reverse("download_document", args=[document.pk])

        anonymous_response = self.client.get(url)
        self.assertEqual(anonymous_response.status_code, 302)
        self.assertIn("/staff/login/", anonymous_response.url)

        farmer_user = get_user_model().objects.create_user(
            username="farmer", password="Strong-test-password-23"
        )
        self.client.force_login(farmer_user)
        farmer_response = self.client.get(url)
        self.assertEqual(farmer_response.status_code, 302)

        staff_user = get_user_model().objects.create_user(
            username="reviewer",
            password="Another-strong-test-password-45",
            is_staff=True,
        )
        self.client.force_login(staff_user)
        staff_response = self.client.get(url)
        self.assertEqual(staff_response.status_code, 200)
        self.assertEqual(staff_response["Content-Type"], "application/octet-stream")
        self.assertEqual(staff_response["X-Content-Type-Options"], "nosniff")
        self.assertIn("attachment", staff_response["Content-Disposition"])
        self.assertTrue(b"".join(staff_response.streaming_content))

    def test_rate_limit_blocks_sixth_registration_post(self):
        for _ in range(5):
            self.client.post(self.url, self.individual_data)

        response = self.client.post(self.url, self.individual_data)

        self.assertEqual(response.status_code, 429)
        self.assertEqual(FarmerProfile.objects.count(), 5)

    def test_retention_command_previews_then_deletes_expired_data(self):
        old_date = timezone.now() - timedelta(days=800)
        profile = FarmerProfile.objects.create(
            registration_type=FarmerProfile.RegistrationType.INDIVIDUAL,
            full_name="Old Sample Farmer",
            preferred_contact=FarmerProfile.ContactPreference.PHONE,
            county="Vihiga",
            privacy_consent_at=old_date,
            created_at=old_date,
            last_contact_at=old_date,
        )
        document = FarmerDocument.objects.create(
            profile=profile,
            document_type=FarmerDocument.DocumentType.FARM,
            uploaded_at=old_date,
        )
        document.file.save("old-evidence.png", png_upload(), save=True)
        stored_path = document.file.path
        recent_profile = FarmerProfile.objects.create(
            registration_type=FarmerProfile.RegistrationType.INDIVIDUAL,
            full_name="Recent Sample Farmer",
            preferred_contact=FarmerProfile.ContactPreference.PHONE,
            county="Vihiga",
            privacy_consent_at=timezone.now(),
            last_contact_at=timezone.now(),
        )
        expired_document = FarmerDocument.objects.create(
            profile=recent_profile,
            document_type=FarmerDocument.DocumentType.FARM,
            uploaded_at=old_date,
        )
        expired_document.file.save("expired-evidence.png", png_upload(), save=True)
        expired_path = expired_document.file.path

        output = StringIO()
        call_command("purge_retained_data", stdout=output)
        self.assertIn("Dry run: 2 document(s) and 1 profile/request(s)", output.getvalue())
        self.assertTrue(FarmerProfile.objects.filter(pk=profile.pk).exists())
        self.assertTrue(FarmerDocument.objects.filter(pk=document.pk).exists())

        with self.captureOnCommitCallbacks(execute=True):
            call_command("purge_retained_data", "--execute")

        self.assertFalse(FarmerProfile.objects.filter(pk=profile.pk).exists())
        self.assertFalse(FarmerDocument.objects.filter(pk=document.pk).exists())
        self.assertTrue(FarmerProfile.objects.filter(pk=recent_profile.pk).exists())
        self.assertFalse(FarmerDocument.objects.filter(pk=expired_document.pk).exists())
        self.assertFalse(Path(stored_path).exists())
        self.assertFalse(Path(expired_path).exists())


class PartnerRegistrationTests(TestCase):
    def setUp(self):
        cache.clear()
        self.private_files = TemporaryDirectory()
        self.addCleanup(self.private_files.cleanup)
        self.settings_override = override_settings(
            MEDIA_ROOT=self.private_files.name,
            PRIVATE_UPLOAD_ROOT=self.private_files.name,
            ANTIVIRUS_ENABLED=False,
        )
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)
        self.url = reverse("register_partner")
        self.data = {
            "applicant_type": "business",
            "contact_name": "Sample Contact",
            "business_name": "Sample Agri Services",
            "preferred_contact": "phone",
            "phone": "0712345678",
            "county": "Vihiga",
            "roles": ["supplier"],
            "offer_categories": ["seeds_seedlings"],
            "offer_details": "Certified vegetable seedlings, available year round.",
            "privacy_consent": "on",
            "documents-TOTAL_FORMS": "1",
            "documents-INITIAL_FORMS": "0",
            "documents-MIN_NUM_FORMS": "0",
            "documents-MAX_NUM_FORMS": "20",
            "documents-0-document_type": "business",
            "documents-0-description": "",
        }

    def test_supplier_registration_is_saved_and_listing_consent_is_optional(self):
        response = self.client.post(self.url, self.data)

        self.assertEqual(response.status_code, 302)
        self.assertRegex(response.url, r"^/portal/partners/registered/[A-F0-9]{8}/$")
        profile = PartnerProfile.objects.get()
        self.assertEqual(profile.roles, ["supplier"])
        self.assertEqual(profile.offer_categories, ["seeds_seedlings"])
        self.assertEqual(
            profile.registration_status,
            PartnerProfile.RegistrationStatus.NOT_REGISTERED,
        )
        self.assertIsNotNone(profile.contact_consent_at)
        self.assertIsNone(profile.listing_referral_consent_at)
        self.assertEqual(
            profile.verification_status,
            PartnerProfile.ReviewStatus.PENDING,
        )

    def test_partner_can_separately_opt_in_to_research_invitations(self):
        response = self.client.post(
            self.url,
            {**self.data, "research_invite_consent": "on"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertIsNotNone(PartnerProfile.objects.get().research_invite_consent_at)

    def test_multi_role_registration_requires_and_saves_each_role_profile(self):
        data = {
            **self.data,
            "roles": ["supplier", "buyer", "service_provider"],
            "produce_categories": ["cereals"],
            "produce_details": "Buying dry maize in clean 90 kg bags.",
            "service_description": "Agronomy training for farmer groups.",
        }
        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, 302)
        profile = PartnerProfile.objects.get()
        self.assertCountEqual(
            profile.roles,
            ["supplier", "buyer", "service_provider"],
        )
        self.assertEqual(profile.produce_categories, ["cereals"])
        self.assertEqual(profile.service_description, "Agronomy training for farmer groups.")

    def test_buyer_and_service_provider_roles_validate_their_own_details(self):
        data = {
            **self.data,
            "roles": ["buyer", "service_provider"],
            "produce_categories": ["cereals"],
            "produce_details": "Buying dry maize in clean 90 kg bags.",
        }
        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(PartnerProfile.objects.count(), 0)
        self.assertContains(response, "Describe your services and the people or areas you serve.")

        data["service_description"] = "Agronomy training for farmer groups."
        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, 302)
        profile = PartnerProfile.objects.get()
        self.assertEqual(profile.roles, ["buyer", "service_provider"])

    def test_partner_evidence_requires_consent_and_staff_only_download(self):
        data = {
            **self.data,
            "documents-TOTAL_FORMS": "1",
            "documents-INITIAL_FORMS": "0",
            "documents-MIN_NUM_FORMS": "0",
            "documents-MAX_NUM_FORMS": "20",
            "documents-0-document_type": "business",
            "documents-0-description": "Synthetic registration evidence",
            "documents-0-file": png_upload(),
        }
        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(PartnerProfile.objects.count(), 0)
        self.assertContains(response, "Please agree to the one-year document retention notice")

        data["documents-0-file"] = png_upload()
        data["document_consent"] = "on"
        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, 302)
        profile = PartnerProfile.objects.get()
        document = PartnerDocument.objects.get(profile=profile)
        self.assertIsNotNone(profile.document_consent_at)
        url = reverse("download_partner_document", args=[document.pk])
        self.assertEqual(self.client.get(url).status_code, 302)

        staff_user = get_user_model().objects.create_user(
            username="partner-reviewer",
            password="test-password",
            is_staff=True,
        )
        self.client.force_login(staff_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["X-Content-Type-Options"], "nosniff")
        self.assertIn("attachment", response["Content-Disposition"])
        self.assertTrue(b"".join(response.streaming_content))

    def test_partner_retention_command_deletes_old_profile_and_private_evidence(self):
        old_date = timezone.now() - timedelta(days=800)
        profile = PartnerProfile.objects.create(
            applicant_type=PartnerProfile.ApplicantType.BUSINESS,
            contact_name="Old Sample Contact",
            business_name="Old Sample Business",
            preferred_contact=PartnerProfile.ContactPreference.PHONE,
            county="Vihiga",
            roles=["supplier"],
            contact_consent_at=old_date,
            created_at=old_date,
            last_contact_at=old_date,
        )
        document = PartnerDocument.objects.create(
            profile=profile,
            document_type=PartnerDocument.DocumentType.BUSINESS,
            uploaded_at=old_date,
        )
        document.file.save("old-partner-evidence.png", png_upload(), save=True)
        stored_path = document.file.path

        output = StringIO()
        call_command("purge_retained_data", stdout=output)
        self.assertIn("1 document(s) and 1 profile/request(s)", output.getvalue())

        with self.captureOnCommitCallbacks(execute=True):
            call_command("purge_retained_data", "--execute")

        self.assertFalse(PartnerProfile.objects.filter(pk=profile.pk).exists())
        self.assertFalse(PartnerDocument.objects.filter(pk=document.pk).exists())
        self.assertFalse(Path(stored_path).exists())


class FinancialAnalysisRequestTests(TestCase):
    def setUp(self):
        cache.clear()
        self.private_files = TemporaryDirectory()
        self.addCleanup(self.private_files.cleanup)
        self.settings_override = override_settings(
            MEDIA_ROOT=self.private_files.name,
            PRIVATE_UPLOAD_ROOT=self.private_files.name,
            ANTIVIRUS_ENABLED=False,
        )
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)
        self.url = reverse("request_financial_analysis")
        self.data = {
            "applicant_type": "business",
            "contact_name": "Synthetic Finance Contact",
            "business_name": "Synthetic Farm Enterprise",
            "phone": "0700000000",
            "preferred_contact": "phone",
            "county": "Vihiga",
            "sector": "Horticulture",
            "services_requested": ["statement_review", "cash_flow"],
            "financial_period": "January to December 2025",
            "records_available": ["cashbook", "sales_records"],
            "annual_revenue_band": "under_500k",
            "funding_need_band": "none",
            "timeline": "flexible",
            "request_summary": "Synthetic request for a sample cash-flow review.",
            "privacy_consent": "on",
            "documents-TOTAL_FORMS": "0",
            "documents-INITIAL_FORMS": "0",
            "documents-MIN_NUM_FORMS": "0",
            "documents-MAX_NUM_FORMS": "20",
        }

    def test_request_is_saved_for_manual_scope_and_quote(self):
        response = self.client.post(self.url, self.data)

        self.assertEqual(response.status_code, 302)
        self.assertRegex(
            response.url,
            r"^/portal/financial-analysis/received/[A-F0-9]{8}/$",
        )
        analysis_request = FinancialAnalysisRequest.objects.get()
        self.assertEqual(
            analysis_request.services_requested,
            ["statement_review", "cash_flow"],
        )
        self.assertEqual(analysis_request.records_available, ["cashbook", "sales_records"])
        self.assertEqual(
            analysis_request.status,
            FinancialAnalysisRequest.ServiceStatus.PENDING,
        )
        self.assertIsNotNone(analysis_request.contact_consent_at)

    def test_selected_contact_method_requires_matching_contact_detail(self):
        data = {
            **self.data,
            "phone": "",
            "email": "",
        }
        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(FinancialAnalysisRequest.objects.count(), 0)
        self.assertContains(response, "A phone number is required for the selected contact method.")

    def test_quote_status_requires_recorded_fee(self):
        analysis_request = FinancialAnalysisRequest.objects.create(
            applicant_type=FinancialAnalysisRequest.ApplicantType.BUSINESS,
            contact_name="Synthetic Finance Contact",
            business_name="Synthetic Farm Enterprise",
            phone="0700000000",
            preferred_contact=FinancialAnalysisRequest.ContactPreference.PHONE,
            county="Vihiga",
            services_requested=["statement_review"],
            request_summary="Synthetic request.",
            contact_consent_at=timezone.now(),
        )
        analysis_request.status = FinancialAnalysisRequest.ServiceStatus.QUOTED

        with self.assertRaises(ValidationError) as error:
            analysis_request.full_clean()
        self.assertIn("quote_amount", error.exception.message_dict)

        analysis_request.quote_amount = "5000.00"
        analysis_request.full_clean()

    def test_staff_can_open_financial_request_in_admin_for_status_management(self):
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, 302)
        analysis_request = FinancialAnalysisRequest.objects.get()
        staff_user = get_user_model().objects.create_user(
            username="finance-admin",
            password="test-password",
            is_staff=True,
            is_superuser=True,
        )
        self.client.force_login(staff_user)

        response = self.client.get(
            reverse(
                "admin:farmers_financialanalysisrequest_change",
                args=[analysis_request.pk],
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "New request")
        self.assertContains(response, "Quoted fee (KES)")

    def test_upload_requires_consent_and_staff_only_access(self):
        pdf = SimpleUploadedFile(
            "synthetic-statement.pdf",
            b"%PDF-1.7 synthetic financial document",
            content_type="application/pdf",
        )
        data = {
            **self.data,
            "documents-TOTAL_FORMS": "1",
            "documents-INITIAL_FORMS": "0",
            "documents-MIN_NUM_FORMS": "0",
            "documents-MAX_NUM_FORMS": "20",
            "documents-0-document_type": "statement",
            "documents-0-description": "Synthetic sample statement",
            "documents-0-file": pdf,
        }
        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(FinancialAnalysisRequest.objects.count(), 0)
        self.assertContains(response, "Please agree to the one-year document retention notice")

        data["documents-0-file"] = SimpleUploadedFile(
            "synthetic-statement.pdf",
            b"%PDF-1.7 synthetic financial document",
            content_type="application/pdf",
        )
        data["document_consent"] = "on"
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)

        analysis_request = FinancialAnalysisRequest.objects.get()
        document = FinancialAnalysisDocument.objects.get(request=analysis_request)
        self.assertIsNotNone(analysis_request.document_consent_at)
        self.assertEqual(self.client.get(document.file.url).status_code, 404)
        download_url = reverse("download_financial_analysis_document", args=[document.pk])
        self.assertEqual(self.client.get(download_url).status_code, 302)

        staff_user = get_user_model().objects.create_user(
            username="finance-reviewer",
            password="test-password",
            is_staff=True,
        )
        self.client.force_login(staff_user)
        response = self.client.get(download_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["X-Content-Type-Options"], "nosniff")
        self.assertIn("attachment", response["Content-Disposition"])
        self.assertIn(b"synthetic financial document", b"".join(response.streaming_content))

    def test_financial_requests_and_documents_are_removed_by_retention_command(self):
        old_date = timezone.now() - timedelta(days=800)
        analysis_request = FinancialAnalysisRequest.objects.create(
            applicant_type=FinancialAnalysisRequest.ApplicantType.BUSINESS,
            contact_name="Old Synthetic Contact",
            business_name="Old Synthetic Enterprise",
            phone="0700000000",
            preferred_contact=FinancialAnalysisRequest.ContactPreference.PHONE,
            county="Vihiga",
            services_requested=["business_plan"],
            request_summary="Synthetic historic request.",
            contact_consent_at=old_date,
            created_at=old_date,
            last_contact_at=old_date,
        )
        document = FinancialAnalysisDocument.objects.create(
            request=analysis_request,
            document_type=FinancialAnalysisDocument.DocumentType.BUSINESS_PLAN,
            uploaded_at=old_date,
        )
        document.file.save(
            "old-synthetic-plan.pdf",
            SimpleUploadedFile("old-synthetic-plan.pdf", b"%PDF-1.7 synthetic"),
            save=True,
        )
        stored_path = document.file.path
        recent_request = FinancialAnalysisRequest.objects.create(
            applicant_type=FinancialAnalysisRequest.ApplicantType.BUSINESS,
            contact_name="Recent Synthetic Contact",
            business_name="Recent Synthetic Enterprise",
            phone="0700000000",
            preferred_contact=FinancialAnalysisRequest.ContactPreference.PHONE,
            county="Vihiga",
            services_requested=["business_plan"],
            request_summary="Synthetic recent request.",
            contact_consent_at=timezone.now(),
        )
        expired_document = FinancialAnalysisDocument.objects.create(
            request=recent_request,
            document_type=FinancialAnalysisDocument.DocumentType.BUSINESS_PLAN,
            uploaded_at=old_date,
        )
        expired_document.file.save(
            "expired-synthetic-plan.pdf",
            SimpleUploadedFile("expired-synthetic-plan.pdf", b"%PDF-1.7 synthetic"),
            save=True,
        )
        expired_document_path = expired_document.file.path

        with self.captureOnCommitCallbacks(execute=True):
            call_command("purge_retained_data", "--execute")

        self.assertFalse(FinancialAnalysisRequest.objects.filter(pk=analysis_request.pk).exists())
        self.assertFalse(FinancialAnalysisDocument.objects.filter(pk=document.pk).exists())
        self.assertFalse(Path(stored_path).exists())
        self.assertTrue(FinancialAnalysisRequest.objects.filter(pk=recent_request.pk).exists())
        self.assertFalse(FinancialAnalysisDocument.objects.filter(pk=expired_document.pk).exists())
        self.assertFalse(Path(expired_document_path).exists())


class RiskAssessmentRequestTests(TestCase):
    def setUp(self):
        cache.clear()
        self.private_files = TemporaryDirectory()
        self.addCleanup(self.private_files.cleanup)
        self.settings_override = override_settings(
            MEDIA_ROOT=self.private_files.name,
            PRIVATE_UPLOAD_ROOT=self.private_files.name,
            ANTIVIRUS_ENABLED=False,
        )
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)
        self.url = reverse("request_risk_assessment")
        self.data = {
            "applicant_type": "business",
            "contact_name": "Synthetic Assessment Contact",
            "business_name": "Synthetic Farm Enterprise",
            "phone": "0700000000",
            "preferred_contact": "phone",
            "county": "Vihiga",
            "sector": "Horticulture",
            "enterprise_stage": "production",
            "assessment_areas": ["enterprise", "market", "climate_environment"],
            "risk_priorities": ["production", "climate"],
            "opportunity_priorities": ["market_growth", "climate_resilience"],
            "time_horizon": "this_year",
            "request_summary": (
                "Synthetic request to understand production risks and potential market growth."
            ),
            "privacy_consent": "on",
            "documents-TOTAL_FORMS": "0",
            "documents-INITIAL_FORMS": "0",
            "documents-MIN_NUM_FORMS": "0",
            "documents-MAX_NUM_FORMS": "20",
        }

    def create_request(self, **overrides):
        values = {
            "applicant_type": RiskAssessmentRequest.ApplicantType.BUSINESS,
            "contact_name": "Synthetic Assessment Contact",
            "business_name": "Synthetic Farm Enterprise",
            "phone": "0700000000",
            "preferred_contact": RiskAssessmentRequest.ContactPreference.PHONE,
            "county": "Vihiga",
            "assessment_areas": ["enterprise"],
            "risk_priorities": ["production"],
            "opportunity_priorities": ["market_growth"],
            "time_horizon": RiskAssessmentRequest.TimeHorizon.THIS_YEAR,
            "request_summary": "Synthetic assessment request.",
            "contact_consent_at": timezone.now(),
        }
        values.update(overrides)
        return RiskAssessmentRequest.objects.create(**values)

    def test_request_is_saved_for_manual_scope_and_fee_quote(self):
        response = self.client.post(self.url, self.data)

        self.assertEqual(response.status_code, 302)
        self.assertRegex(
            response.url,
            r"^/portal/risk-assessment/received/[A-F0-9]{8}/$",
        )
        assessment_request = RiskAssessmentRequest.objects.get()
        self.assertEqual(assessment_request.assessment_areas, ["enterprise", "market", "climate_environment"])
        self.assertEqual(assessment_request.risk_priorities, ["production", "climate"])
        self.assertEqual(
            assessment_request.opportunity_priorities,
            ["market_growth", "climate_resilience"],
        )
        self.assertEqual(
            assessment_request.status,
            RiskAssessmentRequest.ServiceStatus.PENDING,
        )
        self.assertIsNotNone(assessment_request.contact_consent_at)
        self.assertIsNone(assessment_request.quote_amount)

    def test_missing_contact_consent_and_contact_method_details_are_rejected(self):
        response = self.client.post(
            self.url,
            {**self.data, "phone": "", "privacy_consent": ""},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(RiskAssessmentRequest.objects.count(), 0)
        self.assertContains(response, "This field is required.")
        self.assertContains(response, "A phone number is required for the selected contact method.")

    def test_model_rejects_unrecognized_scope_and_quoted_status_without_fee(self):
        assessment_request = self.create_request(assessment_areas=["made_up"])
        with self.assertRaises(ValidationError) as error:
            assessment_request.full_clean()
        self.assertIn("assessment_areas", error.exception.message_dict)

        assessment_request = self.create_request(
            status=RiskAssessmentRequest.ServiceStatus.QUOTED
        )
        with self.assertRaises(ValidationError) as error:
            assessment_request.full_clean()
        self.assertIn("quote_amount", error.exception.message_dict)
        assessment_request.quote_amount = "7500.00"
        assessment_request.full_clean()

    def test_staff_can_review_request_and_record_quote(self):
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, 302)
        assessment_request = RiskAssessmentRequest.objects.get()
        staff_user = get_user_model().objects.create_user(
            username="risk-assessment-reviewer",
            password="Synthetic-Only-Password-123!",
            is_staff=True,
            is_superuser=True,
        )
        self.client.force_login(staff_user)

        response = self.client.get(
            reverse(
                "admin:farmers_riskassessmentrequest_change",
                args=[assessment_request.pk],
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Under initial review")
        self.assertContains(response, "Quoted fee (KES)")

    def test_upload_requires_separate_consent_and_is_staff_only(self):
        data = {
            **self.data,
            "documents-TOTAL_FORMS": "1",
            "documents-INITIAL_FORMS": "0",
            "documents-MIN_NUM_FORMS": "0",
            "documents-MAX_NUM_FORMS": "20",
            "documents-0-document_type": "market",
            "documents-0-description": "Synthetic market summary",
            "documents-0-file": SimpleUploadedFile(
                "synthetic-market-summary.pdf",
                b"%PDF-1.7 synthetic assessment summary",
                content_type="application/pdf",
            ),
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(RiskAssessmentRequest.objects.count(), 0)
        self.assertContains(response, "Please agree to the one-year document retention notice")

        data["document_consent"] = "on"
        data["documents-0-file"] = SimpleUploadedFile(
            "synthetic-market-summary.pdf",
            b"%PDF-1.7 synthetic assessment summary",
            content_type="application/pdf",
        )
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        assessment_request = RiskAssessmentRequest.objects.get()
        document = RiskAssessmentDocument.objects.get(request=assessment_request)
        self.assertIsNotNone(assessment_request.document_consent_at)
        self.assertEqual(self.client.get(document.file.url).status_code, 404)
        download_url = reverse("download_risk_assessment_document", args=[document.pk])
        self.assertEqual(self.client.get(download_url).status_code, 302)

        staff_user = get_user_model().objects.create_user(
            username="risk-document-reviewer",
            password="Synthetic-Only-Password-123!",
            is_staff=True,
        )
        self.client.force_login(staff_user)
        response = self.client.get(download_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["X-Content-Type-Options"], "nosniff")
        self.assertIn("attachment", response["Content-Disposition"])
        self.assertIn(
            b"synthetic assessment summary",
            b"".join(response.streaming_content),
        )

    def test_retention_purges_inactive_request_and_cascades_private_files(self):
        old_date = timezone.now() - timedelta(days=800)
        assessment_request = self.create_request(
            contact_consent_at=old_date,
            created_at=old_date,
            last_contact_at=old_date,
        )
        document = RiskAssessmentDocument.objects.create(
            request=assessment_request,
            document_type=RiskAssessmentDocument.DocumentType.BUSINESS_PROFILE,
        )
        document.file.save(
            "synthetic-assessment-profile.pdf",
            SimpleUploadedFile(
                "synthetic-assessment-profile.pdf",
                b"%PDF-1.7 synthetic assessment profile",
            ),
            save=True,
        )
        stored_path = document.file.path

        with self.captureOnCommitCallbacks(execute=True):
            call_command("purge_retained_data", "--execute")

        self.assertFalse(
            RiskAssessmentRequest.objects.filter(pk=assessment_request.pk).exists()
        )
        self.assertFalse(RiskAssessmentDocument.objects.filter(pk=document.pk).exists())
        self.assertFalse(Path(stored_path).exists())


class ResearchPortalTests(TestCase):
    def setUp(self):
        cache.clear()
        self.url = reverse("register_researcher")

    def researcher_account(self, username="researcher@example.org", approved=True):
        user = get_user_model().objects.create_user(
            username=username,
            email=username,
            password="E!Research-Portal-2026-long-pass",
            is_active=approved,
        )
        application = ResearcherApplication.objects.create(
            user=user,
            applicant_type=ResearcherApplication.ApplicantType.ORGANISATION,
            organisation_name="Synthetic Research Institute",
            phone="0700000000",
            research_purpose="Synthetic market research purpose.",
            methods_summary="Synthetic methods and participant safeguards.",
            consent_at=timezone.now(),
            review_status=(
                ResearcherApplication.ReviewStatus.APPROVED
                if approved
                else ResearcherApplication.ReviewStatus.PENDING
            ),
        )
        return user, application

    def study(self, researcher, title="Synthetic Market Study", status=None):
        now = timezone.now()
        study = ResearchStudy.objects.create(
            researcher=researcher,
            title=title,
            purpose="Understand synthetic crop market preferences.",
            intended_use="Inform a synthetic academic report.",
            methodology="Voluntary fixed-choice questionnaire.",
            target_audiences=[ResearchStudy.Audience.FARMER_INDIVIDUAL],
            target_counties=["Vihiga"],
            target_sample_size=50,
            ethics_status=ResearchStudy.EthicsStatus.NOT_REQUIRED,
            respondent_consent_text=(
                "This study asks about general market preferences. Participation is voluntary."
            ),
            closes_at=now + timedelta(days=14),
            status=status or ResearchStudy.Status.PUBLISHED,
            fee_quote_kes="1500.00",
            fee_accepted_at=now,
        )
        question = ResearchQuestion.objects.create(
            study=study,
            position=1,
            prompt="Which crop do you prefer?",
            answer_type=ResearchQuestion.AnswerType.SINGLE,
            options=["Maize", "Beans"],
            required=True,
        )
        return study, question

    def opt_in_farmer(self, name="Synthetic Research Participant"):
        return FarmerProfile.objects.create(
            registration_type=FarmerProfile.RegistrationType.INDIVIDUAL,
            full_name=name,
            phone="0712345678",
            preferred_contact=FarmerProfile.ContactPreference.PHONE,
            county="Vihiga",
            privacy_consent_at=timezone.now(),
            research_invite_consent_at=timezone.now(),
        )

    def test_researcher_registration_creates_inactive_account_for_manual_vetting(self):
        data = {
            "email": "principal@example.org",
            "password1": "E!Research-Portal-2026-long-pass",
            "password2": "E!Research-Portal-2026-long-pass",
            "applicant_type": "organisation",
            "organisation_name": "Synthetic Research Institute",
            "role_title": "Principal Investigator",
            "phone": "0700000000",
            "country": "Kenya",
            "research_purpose": "Study synthetic market preferences.",
            "methods_summary": "Use voluntary fixed-choice surveys with separate consent.",
            "consent": "on",
        }

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, 302)
        user = get_user_model().objects.get(email="principal@example.org")
        self.assertFalse(user.is_active)
        application = ResearcherApplication.objects.get(user=user)
        self.assertEqual(application.review_status, ResearcherApplication.ReviewStatus.PENDING)
        self.assertIsNotNone(application.consent_at)
        self.assertFalse(self.client.login(username=user.email, password=data["password1"]))
        self.assertEqual(
            self.client.get(reverse("researcher_dashboard")).status_code,
            302,
        )

    def test_student_application_requires_supervisor_details(self):
        data = {
            "email": "student@example.org",
            "password1": "E!Research-Portal-2026-long-pass",
            "password2": "E!Research-Portal-2026-long-pass",
            "applicant_type": "student",
            "organisation_name": "Synthetic University",
            "role_title": "Research student",
            "phone": "0700000000",
            "country": "Kenya",
            "research_purpose": "Synthetic student research.",
            "methods_summary": "Synthetic survey method.",
            "consent": "on",
        }

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(get_user_model().objects.filter(email=data["email"]).exists())
        self.assertContains(response, "Student applications require a supervisor.")
        self.assertContains(response, "Provide the supervisor&#x27;s institutional email.")

    def test_admin_vetting_activates_researcher_account(self):
        user, application = self.researcher_account(approved=False)
        staff_user = get_user_model().objects.create_superuser(
            username="research-staff",
            email="research-staff@example.org",
            password="Test-admin-pass-2026!",
        )
        self.client.force_login(staff_user)
        response = self.client.post(
            reverse("admin:farmers_researcherapplication_change", args=[application.pk]),
            {
                "applicant_type": "organisation",
                "organisation_name": "Synthetic Research Institute",
                "role_title": "Principal Investigator",
                "phone": "0700000000",
                "website": "",
                "country": "Kenya",
                "supervisor_name": "",
                "supervisor_email": "",
                "research_purpose": "Synthetic market research purpose.",
                "methods_summary": "Synthetic methods and participant safeguards.",
                "privacy_policy_url": "",
                "data_protection_contact": "",
                "review_status": "approved",
                "review_notes": "Synthetic vetting completed.",
                "_save": "Save",
            },
        )

        self.assertEqual(response.status_code, 302)
        user.refresh_from_db()
        application.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertEqual(application.review_status, ResearcherApplication.ReviewStatus.APPROVED)
        self.assertEqual(application.reviewed_by, staff_user)
        self.client.force_login(user)
        self.assertEqual(self.client.get(reverse("researcher_dashboard")).status_code, 200)

    def test_researcher_can_submit_study_and_fixed_choice_questions(self):
        user, _ = self.researcher_account()
        self.client.force_login(user)
        closes_at = timezone.localtime(timezone.now() + timedelta(days=10)).strftime(
            "%Y-%m-%dT%H:%M"
        )
        data = {
            "title": "Synthetic crop preferences",
            "purpose": "Measure synthetic crop preferences.",
            "intended_use": "Prepare a synthetic report.",
            "methodology": "Voluntary anonymous fixed-choice survey.",
            "target_audiences": ["farmer_individual"],
            "target_counties": ["Vihiga"],
            "target_sample_size": "50",
            "ethics_status": "not_required",
            "respondent_consent_text": "Participation is voluntary and answers are aggregated.",
            "closes_at": closes_at,
            "questions-TOTAL_FORMS": "1",
            "questions-INITIAL_FORMS": "0",
            "questions-MIN_NUM_FORMS": "1",
            "questions-MAX_NUM_FORMS": "12",
            "questions-0-prompt": "Which crop do you prefer?",
            "questions-0-answer_type": "single",
            "questions-0-options_text": "Maize\nBeans",
        }

        response = self.client.post(reverse("researcher_dashboard"), data)

        self.assertEqual(response.status_code, 302)
        study = ResearchStudy.objects.get()
        self.assertEqual(study.status, ResearchStudy.Status.SUBMITTED)
        self.assertEqual(study.questions.count(), 1)
        self.assertEqual(study.questions.get().options, ["Maize", "Beans"])
        self.assertFalse(ResearchInvitation.objects.exists())

    def test_only_opted_in_target_members_can_receive_study_invitations(self):
        _, researcher = self.researcher_account()
        study, _ = self.study(researcher)
        opted_out = FarmerProfile.objects.create(
            registration_type=FarmerProfile.RegistrationType.INDIVIDUAL,
            full_name="Opted Out Farmer",
            preferred_contact=FarmerProfile.ContactPreference.PHONE,
            county="Vihiga",
            privacy_consent_at=timezone.now(),
        )
        invitation = ResearchInvitation(study=study, farmer_profile=opted_out)

        with self.assertRaises(ValidationError) as error:
            invitation.full_clean()
        self.assertIn("farmer_profile", error.exception.message_dict)

        opted_in = self.opt_in_farmer()
        invitation = ResearchInvitation(study=study, farmer_profile=opted_in)
        invitation.full_clean()
        invitation.save()
        self.assertTrue(invitation.token)
        self.assertEqual(invitation.expires_at.date(), (timezone.now() + timedelta(days=14)).date())

    def test_response_requires_separate_consent_and_removes_member_link(self):
        _, researcher = self.researcher_account()
        study, question = self.study(researcher)
        participant = self.opt_in_farmer()
        invitation = ResearchInvitation.objects.create(study=study, farmer_profile=participant)
        url = reverse("respond_to_research_invitation", args=[invitation.token])
        self.assertEqual(self.client.get(url).status_code, 200)

        data = {f"question_{question.pk}": "Maize"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ResearchResponse.objects.count(), 0)
        invitation.refresh_from_db()
        self.assertIsNone(invitation.completed_on)

        data["participant_consent"] = "on"
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Thank you for participating")
        research_response = ResearchResponse.objects.get(study=study)
        self.assertEqual(research_response.answers, {str(question.pk): "Maize"})
        self.assertFalse(
            {"phone", "email", "full_name", "farmer_profile", "partner_profile"}
            & set(research_response.answers)
        )
        invitation.refresh_from_db()
        self.assertIsNotNone(invitation.completed_on)
        self.assertIsNone(invitation.farmer_profile)
        self.assertIsNone(invitation.partner_profile)
        self.assertEqual(self.client.get(url).status_code, 410)

    def test_withdrawing_research_invitation_consent_invalidates_outstanding_link(self):
        _, researcher = self.researcher_account()
        study, _ = self.study(researcher)
        participant = self.opt_in_farmer()
        invitation = ResearchInvitation.objects.create(study=study, farmer_profile=participant)
        participant.research_invite_consent_at = None
        participant.save(update_fields=["research_invite_consent_at"])

        response = self.client.get(
            reverse("respond_to_research_invitation", args=[invitation.token])
        )

        self.assertEqual(response.status_code, 410)

    def test_researcher_dashboard_suppresses_small_cells_and_hides_individual_answers(self):
        user, application = self.researcher_account()
        suppressed_study, suppressed_question = self.study(
            application,
            title="Small cells study",
            status=ResearchStudy.Status.CLOSED,
        )
        visible_study, visible_question = self.study(
            application,
            title="Aggregate only study",
            status=ResearchStudy.Status.CLOSED,
        )
        for answer in ["Maize", "Maize", "Maize", "Beans", "Beans"]:
            ResearchResponse.objects.create(
                study=suppressed_study,
                answers={str(suppressed_question.pk): answer},
            )
        for _ in range(5):
            ResearchResponse.objects.create(
                study=visible_study,
                answers={str(visible_question.pk): "Maize"},
            )

        self.client.force_login(user)
        response = self.client.get(reverse("researcher_dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Results withheld because one or more answer categories contain fewer than five responses.",
        )
        self.assertContains(response, "Maize: 5")
        self.assertNotContains(response, "Individual response records")
        self.assertNotContains(response, "research_response")

    def test_retention_purges_old_responses_expired_invites_and_inactive_researchers(self):
        user, application = self.researcher_account(approved=False)
        old_date = timezone.now() - timedelta(days=800)
        application.last_contact_at = old_date
        application.save(update_fields=["last_contact_at"])
        study, question = self.study(
            application,
            title="Old retained study",
            status=ResearchStudy.Status.CLOSED,
        )
        ResearchResponse.objects.create(
            study=study,
            answers={str(question.pk): "Maize"},
            submitted_on=timezone.localdate() - timedelta(days=400),
        )
        participant = self.opt_in_farmer("Expired invite participant")
        invitation = ResearchInvitation.objects.create(
            study=study,
            farmer_profile=participant,
            expires_at=timezone.now() - timedelta(days=1),
        )

        output = StringIO()
        with self.captureOnCommitCallbacks(execute=True):
            call_command("purge_retained_data", "--execute", stdout=output)

        self.assertFalse(get_user_model().objects.filter(pk=user.pk).exists())
        self.assertFalse(ResearchResponse.objects.filter(study=study).exists())
        self.assertFalse(ResearchInvitation.objects.filter(pk=invitation.pk).exists())
        self.assertIn(
            "1 research study record(s), 1 research response record(s), and "
            "1 invitation record(s)",
            output.getvalue(),
        )
