import hashlib
import hmac
import json

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import FarmerProfile, WhatsAppLocationPing

APP_SECRET = "test-whatsapp-app-secret"
VERIFY_TOKEN = "test-verify-token"


def signed_post(client, url, payload):
    body = json.dumps(payload).encode("utf-8")
    signature = hmac.new(APP_SECRET.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return client.post(
        url,
        data=body,
        content_type="application/json",
        HTTP_X_HUB_SIGNATURE_256=f"sha256={signature}",
    )


def location_payload(message_id, from_number, latitude=-0.0917, longitude=34.7297):
    return {
        "entry": [{
            "changes": [{
                "value": {
                    "messages": [{
                        "id": message_id,
                        "from": from_number,
                        "type": "location",
                        "location": {"latitude": latitude, "longitude": longitude},
                    }]
                }
            }]
        }]
    }


@override_settings(WHATSAPP_APP_SECRET=APP_SECRET, WHATSAPP_VERIFY_TOKEN=VERIFY_TOKEN)
class WhatsAppWebhookTests(TestCase):
    def setUp(self):
        self.url = reverse("whatsapp_webhook")
        self.profile = FarmerProfile.objects.create(
            registration_type=FarmerProfile.RegistrationType.INDIVIDUAL,
            full_name="Pin Farmer",
            phone="0712345678",
            preferred_contact=FarmerProfile.ContactPreference.PHONE,
            county="Vihiga",
            privacy_consent_at=timezone.now(),
        )

    def test_verification_handshake_returns_challenge_for_correct_token(self):
        response = self.client.get(
            self.url,
            {"hub.mode": "subscribe", "hub.verify_token": VERIFY_TOKEN, "hub.challenge": "12345"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "12345")

    def test_verification_handshake_rejects_wrong_token(self):
        response = self.client.get(
            self.url,
            {"hub.mode": "subscribe", "hub.verify_token": "wrong", "hub.challenge": "12345"},
        )

        self.assertEqual(response.status_code, 403)

    def test_post_rejects_missing_or_invalid_signature(self):
        body = json.dumps(location_payload("wamid.1", "254712345678")).encode("utf-8")
        response = self.client.post(self.url, data=body, content_type="application/json")

        self.assertEqual(response.status_code, 403)
        self.assertEqual(WhatsAppLocationPing.objects.count(), 0)

    def test_valid_location_message_is_recorded_and_matched_by_phone(self):
        response = signed_post(
            self.client, self.url, location_payload("wamid.2", "254712345678")
        )

        self.assertEqual(response.status_code, 200)
        ping = WhatsAppLocationPing.objects.get()
        self.assertEqual(ping.matched_profile, self.profile)
        self.profile.refresh_from_db()
        self.assertEqual(float(self.profile.farm_latitude), -0.0917)
        self.assertEqual(float(self.profile.farm_longitude), 34.7297)
        self.assertIsNotNone(self.profile.location_shared_at)

    def test_location_from_unknown_number_is_recorded_without_a_match(self):
        response = signed_post(
            self.client, self.url, location_payload("wamid.3", "254799999999")
        )

        self.assertEqual(response.status_code, 200)
        ping = WhatsAppLocationPing.objects.get()
        self.assertIsNone(ping.matched_profile)
        self.profile.refresh_from_db()
        self.assertIsNone(self.profile.farm_latitude)

    def test_duplicate_message_id_is_recorded_only_once(self):
        signed_post(self.client, self.url, location_payload("wamid.4", "254712345678"))
        response = signed_post(
            self.client, self.url, location_payload("wamid.4", "254712345678")
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(WhatsAppLocationPing.objects.count(), 1)


class WhatsAppWebhookNotConfiguredTests(TestCase):
    def test_webhook_returns_503_when_not_configured(self):
        response = self.client.get(reverse("whatsapp_webhook"))

        self.assertEqual(response.status_code, 503)
