from datetime import timedelta
from decimal import Decimal
from io import BytesIO, StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image, PngImagePlugin

from .models import (
    BusinessReadinessDraft,
    ConsultationLead,
    FarmerDocument,
    FarmerProfile,
    FinancialAnalysisDocument,
    FinancialAnalysisRequest,
    NewsletterSubscription,
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
from .readiness_drafting import (
    build_ai_draft_context,
    save_readiness_draft,
    validate_ai_draft_output,
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


class FarmerAccountTests(TestCase):
    def setUp(self):
        cache.clear()
        self.url = reverse("register_farmer")
        self.individual_data = {
            "registration_type": "individual",
            "full_name": "Account Farmer",
            "phone": "0712345678",
            "preferred_contact": "phone",
            "county": "Vihiga",
            "privacy_consent": "on",
            "documents-TOTAL_FORMS": "0",
            "documents-INITIAL_FORMS": "0",
            "documents-MIN_NUM_FORMS": "0",
            "documents-MAX_NUM_FORMS": "20",
        }

    def test_registration_without_account_checkbox_creates_no_user(self):
        response = self.client.post(self.url, self.individual_data)

        self.assertEqual(response.status_code, 302)
        profile = FarmerProfile.objects.get()
        self.assertIsNone(profile.user)

    def test_registration_with_account_creates_user_and_signs_in(self):
        data = {
            **self.individual_data,
            "email": "account.farmer@example.com",
            "create_account": "on",
            "password1": "a-strong-unique-pass1",
            "password2": "a-strong-unique-pass1",
        }

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("farmer_dashboard"))
        profile = FarmerProfile.objects.get()
        self.assertIsNotNone(profile.user)
        self.assertEqual(profile.user.email, "account.farmer@example.com")
        self.assertTrue(profile.user.check_password("a-strong-unique-pass1"))

        dashboard_response = self.client.get(reverse("farmer_dashboard"))
        self.assertEqual(dashboard_response.status_code, 200)
        self.assertContains(dashboard_response, "Account Farmer")

    def test_account_creation_requires_matching_passwords(self):
        data = {
            **self.individual_data,
            "email": "mismatch@example.com",
            "create_account": "on",
            "password1": "a-strong-unique-pass1",
            "password2": "a-different-pass2",
        }

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(FarmerProfile.objects.count(), 0)
        self.assertContains(response, "The passwords do not match.")

    def test_account_creation_requires_email(self):
        data = {
            **self.individual_data,
            "create_account": "on",
            "password1": "a-strong-unique-pass1",
            "password2": "a-strong-unique-pass1",
        }

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(FarmerProfile.objects.count(), 0)
        self.assertContains(response, "Enter an email address to create an account.")

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("farmer_dashboard"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("farmer_login"), response.url)

    def test_login_with_created_account(self):
        data = {
            **self.individual_data,
            "email": "signin.farmer@example.com",
            "create_account": "on",
            "password1": "a-strong-unique-pass1",
            "password2": "a-strong-unique-pass1",
        }
        self.client.post(self.url, data)
        self.client.logout()

        response = self.client.post(
            reverse("farmer_login"),
            {"username": "signin.farmer@example.com", "password": "a-strong-unique-pass1"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("farmer_dashboard"))


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


class BusinessReadinessPilotTests(TestCase):
    def setUp(self):
        cache.clear()
        self.private_files = TemporaryDirectory()
        self.addCleanup(self.private_files.cleanup)
        settings_override = override_settings(
            MEDIA_ROOT=self.private_files.name,
            PRIVATE_UPLOAD_ROOT=self.private_files.name,
            ANTIVIRUS_ENABLED=False,
        )
        settings_override.enable()
        self.addCleanup(settings_override.disable)
        self.data = {
            "applicant_type": "business",
            "contact_name": "Synthetic Readiness Contact",
            "business_name": "Synthetic Readiness Farm",
            "phone": "0700000000",
            "preferred_contact": "phone",
            "county": "Vihiga",
            "sector": "Horticulture",
            "business_goal": "Improve seasonal planning.",
            "current_challenge": "Sales and costs are not tracked consistently.",
            "average_monthly_sales": "50000",
            "average_monthly_costs": "30000",
            "financial_period": "January to March 2026",
            "records_available": ["sales_records", "expense_records"],
            "annual_revenue_band": "under_500k",
            "seasonality_notes": "Sales rise during harvest.",
            "privacy_consent": "on",
            "documents-TOTAL_FORMS": "0",
            "documents-INITIAL_FORMS": "0",
            "documents-MIN_NUM_FORMS": "0",
            "documents-MAX_NUM_FORMS": "20",
        }

    def test_pilot_intake_creates_a_staff_reviewable_request_without_published_price(self):
        response = self.client.post(reverse("request_business_readiness"), self.data)

        self.assertEqual(response.status_code, 302)
        self.assertRegex(
            response.url,
            r"^/portal/business-readiness/received/[A-F0-9]{8}/$",
        )
        readiness_request = FinancialAnalysisRequest.objects.get()
        self.assertEqual(
            readiness_request.request_type,
            FinancialAnalysisRequest.RequestType.BUSINESS_READINESS,
        )
        self.assertEqual(readiness_request.services_requested, [
            "business_plan",
            "cash_flow",
            "funding_readiness",
        ])
        self.assertEqual(readiness_request.average_monthly_sales, Decimal("50000"))
        self.assertEqual(readiness_request.status, FinancialAnalysisRequest.ServiceStatus.PENDING)
        self.assertFalse(BusinessReadinessDraft.objects.exists())

        page = self.client.get(reverse("request_business_readiness"))
        self.assertContains(page, "No price or delivery time is published")
        self.assertContains(page, "no external AI service connected")

    def test_monthly_cash_flow_inputs_must_be_paired(self):
        response = self.client.post(
            reverse("request_business_readiness"),
            {**self.data, "average_monthly_costs": ""},
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(FinancialAnalysisRequest.objects.exists())
        self.assertContains(response, "Enter both monthly sales and monthly costs")

    def test_staff_draft_uses_cited_inputs_and_fixed_arithmetic(self):
        response = self.client.post(reverse("request_business_readiness"), self.data)
        self.assertEqual(response.status_code, 302)
        readiness_request = FinancialAnalysisRequest.objects.get()
        staff_user = get_user_model().objects.create_user(
            username="readiness-reviewer",
            password="synthetic-test-password",
            is_staff=True,
        )

        draft = save_readiness_draft(readiness_request, staff_user)

        self.assertEqual(draft.generation_method, "rules-v1")
        self.assertEqual(draft.review_status, BusinessReadinessDraft.ReviewStatus.DRAFT)
        self.assertEqual(draft.generated_by, staff_user)
        self.assertEqual(draft.cash_flow["estimated_monthly_difference"], "20,000.00")
        self.assertEqual(draft.cash_flow["annualised_sales_arithmetic"], "600,000.00")
        self.assertEqual(draft.cash_flow["annualised_costs_arithmetic"], "360,000.00")
        citations = {item["id"]: item for item in draft.source_citations}
        self.assertEqual(citations["business_goal"]["source_type"], "customer_input")
        self.assertEqual(
            citations["estimated_monthly_difference"]["formula"],
            "average_monthly_sales - average_monthly_costs",
        )
        self.assertTrue(
            any(
                "annual_revenue_band" in gap["source_refs"]
                for gap in draft.key_gaps
            )
        )
        self.assertFalse(self.client.get(reverse("request_business_readiness")).wsgi_request.user.is_staff)

    def test_staff_approved_draft_cannot_be_overwritten_by_regeneration(self):
        response = self.client.post(reverse("request_business_readiness"), self.data)
        self.assertEqual(response.status_code, 302)
        readiness_request = FinancialAnalysisRequest.objects.get()
        staff_user = get_user_model().objects.create_user(
            username="readiness-approver",
            password="synthetic-test-password",
            is_staff=True,
        )
        draft = save_readiness_draft(readiness_request, staff_user)
        draft.review_status = BusinessReadinessDraft.ReviewStatus.APPROVED
        with self.assertRaises(ValidationError):
            draft.save()
        draft.review_notes = "Reviewed against the submitted information."
        draft.save()

        with self.assertRaises(ValidationError):
            save_readiness_draft(readiness_request, staff_user)

    def test_future_ai_context_minimizes_personal_data_and_validates_citations(self):
        response = self.client.post(reverse("request_business_readiness"), self.data)
        self.assertEqual(response.status_code, 302)
        readiness_request = FinancialAnalysisRequest.objects.get()
        context = build_ai_draft_context(readiness_request)
        source_ids = {source["id"] for source in context["source_data"]}

        self.assertNotIn("Synthetic Readiness Contact", str(context))
        self.assertNotIn("0700000000", str(context))
        self.assertEqual(context["approved_guidance"], [])
        self.assertIn("calculated_values", context)
        output = {
            "business_summary": {
                "text": "The stated challenge is record keeping.",
                "source_refs": ["current_challenge"],
            },
            "key_gaps": [
                {
                    "text": "The challenge was reported by the customer.",
                    "source_refs": ["current_challenge"],
                }
            ],
            "next_steps": [
                {
                    "text": "Review the reported challenge with the customer.",
                    "source_refs": ["current_challenge"],
                }
            ],
            "citations": [
                {
                    "source_id": "current_challenge",
                    "claim": "Customer-described challenge",
                }
            ],
        }
        self.assertEqual(validate_ai_draft_output(output, source_ids), output)
        output["citations"][0]["source_id"] = "unprovided_guidance"
        with self.assertRaises(ValidationError):
            validate_ai_draft_output(output, source_ids)

    def test_staff_can_review_internal_draft_in_admin(self):
        response = self.client.post(reverse("request_business_readiness"), self.data)
        self.assertEqual(response.status_code, 302)
        readiness_request = FinancialAnalysisRequest.objects.get()
        staff_user = get_user_model().objects.create_user(
            username="readiness-admin",
            password="synthetic-test-password",
            is_staff=True,
            is_superuser=True,
        )
        save_readiness_draft(readiness_request, staff_user)
        self.client.force_login(staff_user)

        response = self.client.get(
            reverse(
                "admin:farmers_financialanalysisrequest_change",
                args=[readiness_request.pk],
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Draft — staff review required")
        self.assertContains(response, "Annualised sales arithmetic")
        self.assertContains(response, "rules-v1")


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


class ConsultationLeadTests(TestCase):
    def setUp(self):
        cache.clear()
        self.url = reverse("consultation_lead")
        self.valid_data = {
            "full_name": "Amina Farmer",
            "preferred_contact": "email",
            "email": "amina@example.com",
            "phone": "",
            "organisation_or_county": "Vihiga",
            "category": ConsultationLead.Category.AGRIBUSINESS,
            "message": "I would like to discuss farm planning.",
            "privacy_consent": "on",
            "website": "",
        }

    def test_homepage_renders_database_backed_consultation_form(self):
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'class="logo site-logo"')
        self.assertContains(response, 'alt="MoFirms" width="195" height="65"')
        self.assertContains(response, '<span class="site-logo-name">Marks Organic Farms Concepts Limited</span>')
        self.assertContains(response, 'method="post"')
        self.assertContains(response, 'name="csrfmiddlewaretoken"')
        self.assertContains(response, "No email or SMS automation is configured")
        self.assertRegex(
            response.content.decode(),
            r"/static/images/mofirms-company-logo\.[a-f0-9]+\.png",
        )
        self.assertContains(response, "Marks Organic Farms Concepts Limited")

    def test_demo_homepage_disables_lead_form_and_warns_visitors(self):
        with override_settings(DEMO_MODE=True):
            response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "currently a read-only demo")
        self.assertContains(response, "<fieldset disabled>")

    def test_valid_enquiry_is_saved_for_staff_follow_up(self):
        response = self.client.post(self.url, self.valid_data)

        self.assertEqual(response.status_code, 302)
        lead = ConsultationLead.objects.get()
        self.assertEqual(lead.full_name, "Amina Farmer")
        self.assertEqual(lead.status, ConsultationLead.Status.NEW)
        self.assertEqual(lead.category, ConsultationLead.Category.AGRIBUSINESS)
        self.assertIsNotNone(lead.privacy_consent_at)
        self.assertRegex(response.url, rf"^/portal/consultation/received/{lead.public_reference}/$")

        received = self.client.get(response.url)
        self.assertEqual(received.status_code, 200)
        self.assertContains(received, lead.public_reference)

    def test_phone_contact_requires_a_phone_number(self):
        response = self.client.post(
            self.url,
            {**self.valid_data, "preferred_contact": "phone", "email": ""},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(ConsultationLead.objects.count(), 0)
        self.assertContains(response, "A phone number is required", status_code=400)

    def test_email_contact_requires_a_valid_email(self):
        response = self.client.post(
            self.url,
            {**self.valid_data, "email": "not-an-email"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(ConsultationLead.objects.count(), 0)
        self.assertContains(response, "Enter a valid email address", status_code=400)

    def test_privacy_consent_and_honeypot_are_enforced(self):
        missing_consent = self.client.post(
            self.url,
            {key: value for key, value in self.valid_data.items() if key != "privacy_consent"},
        )
        self.assertEqual(missing_consent.status_code, 400)
        self.assertEqual(ConsultationLead.objects.count(), 0)

        honeypot = self.client.post(
            self.url,
            {**self.valid_data, "website": "automated submission"},
        )
        self.assertEqual(honeypot.status_code, 400)
        self.assertEqual(ConsultationLead.objects.count(), 0)

    def test_demo_mode_keeps_enquiry_submission_disabled(self):
        with override_settings(DEMO_MODE=True):
            response = self.client.post(self.url, self.valid_data)

        self.assertEqual(response.status_code, 405)
        self.assertEqual(ConsultationLead.objects.count(), 0)

    def test_staff_can_review_new_enquiries_in_admin(self):
        self.client.post(self.url, self.valid_data)
        staff_user = get_user_model().objects.create_user(
            username="consultation-reviewer",
            password="test-password-for-local-suite",
            is_staff=True,
        )
        staff_user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="farmers",
                codename="view_consultationlead",
            )
        )
        self.client.force_login(staff_user)

        response = self.client.get(reverse("admin:farmers_consultationlead_changelist"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Amina Farmer")

    def test_rate_limit_blocks_sixth_enquiry(self):
        for _ in range(5):
            self.client.post(self.url, self.valid_data)

        response = self.client.post(self.url, self.valid_data)

        self.assertEqual(response.status_code, 429)
        self.assertEqual(ConsultationLead.objects.count(), 5)

    def test_retention_command_deletes_only_leads_inactive_for_two_years(self):
        lead_data = {
            key: value
            for key, value in self.valid_data.items()
            if key not in {"privacy_consent", "website"}
        }
        old_lead = ConsultationLead.objects.create(
            **lead_data,
            privacy_consent_at=timezone.now(),
            last_contact_at=timezone.now() - timedelta(days=731),
        )
        recent_lead = ConsultationLead.objects.create(
            **{**lead_data, "full_name": "Recent Farmer"},
            privacy_consent_at=timezone.now(),
            last_contact_at=timezone.now(),
        )
        output = StringIO()

        call_command("purge_retained_data", stdout=output)
        self.assertIn("1 consultation enquiry/enquiries", output.getvalue())

        call_command("purge_retained_data", "--execute", stdout=output)
        self.assertFalse(ConsultationLead.objects.filter(pk=old_lead.pk).exists())
        self.assertTrue(ConsultationLead.objects.filter(pk=recent_lead.pk).exists())


@override_settings(
    DJANGO_ENVIRONMENT="production",
    NEWSLETTER_SIGNUPS_ENABLED=True,
)
class NewsletterSubscriptionTests(TestCase):
    def setUp(self):
        cache.clear()
        self.url = reverse("subscribe_newsletter")
        self.valid_data = {
            "email": "Amina@example.com",
            "topics": [
                NewsletterSubscription.Topic.FARMING,
                NewsletterSubscription.Topic.RISK_ASSESSMENT,
            ],
            "marketing_consent": "on",
            "website": "",
        }

    def test_homepage_renders_topic_choices_and_demo_disables_signup(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "News and practical insights")
        self.assertContains(response, "Farming and agribusiness")
        self.assertContains(response, "Entrepreneurship and business advisory")
        self.assertContains(response, "Business risk assessment")

        with override_settings(DEMO_MODE=True):
            demo_response = self.client.get(reverse("home"))
        self.assertContains(demo_response, "Newsletter signups aren’t open on this site yet")
        self.assertContains(demo_response, '<fieldset disabled>')

    def test_signup_requires_explicit_consent_and_selected_topics(self):
        missing_consent = self.client.post(
            self.url,
            {key: value for key, value in self.valid_data.items() if key != "marketing_consent"},
        )
        self.assertEqual(missing_consent.status_code, 400)
        self.assertEqual(NewsletterSubscription.objects.count(), 0)

        missing_topics = self.client.post(
            self.url,
            {**self.valid_data, "topics": ""},
        )
        self.assertEqual(missing_topics.status_code, 400)
        self.assertEqual(NewsletterSubscription.objects.count(), 0)

    def test_signup_saves_normalized_email_topics_and_unsubscribe_link(self):
        response = self.client.post(self.url, self.valid_data)

        self.assertEqual(response.status_code, 200)
        subscription = NewsletterSubscription.objects.get()
        self.assertEqual(subscription.email, "amina@example.com")
        self.assertEqual(
            subscription.topics,
            [
                NewsletterSubscription.Topic.FARMING,
                NewsletterSubscription.Topic.RISK_ASSESSMENT,
            ],
        )
        self.assertEqual(subscription.status, NewsletterSubscription.Status.ACTIVE)
        self.assertIsNotNone(subscription.consent_at)
        self.assertIn(
            reverse("unsubscribe_newsletter", args=(subscription.unsubscribe_token,)),
            response.content.decode(),
        )
        self.assertEqual(response["Cache-Control"], "no-store")
        self.assertEqual(response["Referrer-Policy"], "no-referrer")

    def test_resubscription_requires_consent_and_rotates_old_unsubscribe_link(self):
        self.client.post(self.url, self.valid_data)
        subscription = NewsletterSubscription.objects.get()
        old_token = subscription.unsubscribe_token
        subscription.status = NewsletterSubscription.Status.UNSUBSCRIBED
        subscription.unsubscribed_at = timezone.now()
        subscription.save()

        response = self.client.post(
            self.url,
            {
                **self.valid_data,
                "topics": [NewsletterSubscription.Topic.ENTREPRENEURSHIP],
            },
        )

        self.assertEqual(response.status_code, 200)
        subscription.refresh_from_db()
        self.assertEqual(subscription.status, NewsletterSubscription.Status.ACTIVE)
        self.assertIsNone(subscription.unsubscribed_at)
        self.assertNotEqual(subscription.unsubscribe_token, old_token)
        self.assertEqual(subscription.topics, [NewsletterSubscription.Topic.ENTREPRENEURSHIP])

    def test_unsubscribe_requires_post_confirmation(self):
        self.client.post(self.url, self.valid_data)
        subscription = NewsletterSubscription.objects.get()
        unsubscribe_url = reverse(
            "unsubscribe_newsletter",
            args=(subscription.unsubscribe_token,),
        )

        confirmation = self.client.get(unsubscribe_url)
        self.assertEqual(confirmation.status_code, 200)
        subscription.refresh_from_db()
        self.assertEqual(subscription.status, NewsletterSubscription.Status.ACTIVE)

        result = self.client.post(unsubscribe_url)
        self.assertEqual(result.status_code, 200)
        subscription.refresh_from_db()
        self.assertEqual(subscription.status, NewsletterSubscription.Status.UNSUBSCRIBED)
        self.assertIsNotNone(subscription.unsubscribed_at)

        stale_link = self.client.get(unsubscribe_url)
        self.assertEqual(stale_link.status_code, 404)

    def test_demo_mode_rejects_submissions(self):
        with override_settings(DEMO_MODE=True):
            response = self.client.post(self.url, self.valid_data)

        self.assertEqual(response.status_code, 405)
        self.assertEqual(NewsletterSubscription.objects.count(), 0)

    def test_signups_are_closed_until_explicitly_enabled(self):
        with override_settings(NEWSLETTER_SIGNUPS_ENABLED=False):
            page = self.client.get(reverse("home"))
            response = self.client.post(self.url, self.valid_data)

        self.assertContains(page, "Newsletter signups aren’t open on this site yet")
        self.assertEqual(response.status_code, 405)

        with override_settings(DJANGO_ENVIRONMENT="staging"):
            staging_response = self.client.post(self.url, self.valid_data)
        self.assertEqual(staging_response.status_code, 405)
        self.assertEqual(NewsletterSubscription.objects.count(), 0)

    def test_honeypot_and_rate_limit_block_automated_signups(self):
        honeypot = self.client.post(
            self.url,
            {**self.valid_data, "website": "automated submission"},
        )
        self.assertEqual(honeypot.status_code, 400)
        self.assertEqual(NewsletterSubscription.objects.count(), 0)
        cache.clear()

        for index in range(5):
            self.client.post(
                self.url,
                {**self.valid_data, "email": f"reader{index}@example.com"},
            )
        limited = self.client.post(
            self.url,
            {**self.valid_data, "email": "last@example.com"},
        )
        self.assertEqual(limited.status_code, 429)
        self.assertEqual(NewsletterSubscription.objects.count(), 5)

    def test_staff_can_review_subscribers_in_admin(self):
        self.client.post(self.url, self.valid_data)
        staff_user = get_user_model().objects.create_user(
            username="newsletter-reviewer",
            password="newsletter-test-password",
            is_staff=True,
        )
        staff_user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="farmers",
                codename="view_newslettersubscription",
            )
        )
        self.client.force_login(staff_user)

        response = self.client.get(
            reverse("admin:farmers_newslettersubscription_changelist")
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "amina@example.com")
