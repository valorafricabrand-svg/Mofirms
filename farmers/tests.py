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

from .models import FarmerDocument, FarmerProfile


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
        self.assertIn("Dry run: 2 document(s) and 1 profile(s)", output.getvalue())
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
