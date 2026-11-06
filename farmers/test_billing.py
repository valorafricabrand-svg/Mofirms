import json
from datetime import timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .billing import PaymentForm
from .models import (
    BetaEnrollment,
    BetaInvite,
    FarmerProfile,
    MpesaPayment,
    PartnerProfile,
    ServicePlan,
)
from .mpesa import MpesaError, normalize_phone_number


class PrivateBetaPaymentTests(TestCase):
    def setUp(self):
        self.plan = ServicePlan.objects.create(
            slug="test-plan",
            name="Test plan",
            price=Decimal("12500"),
            tagline="Testing",
            description="Test scope.",
            features=["One advisory session"],
        )
        self.profile = FarmerProfile.objects.create(
            registration_type=FarmerProfile.RegistrationType.INDIVIDUAL,
            full_name="Verified Test Farmer",
            phone="0712345678",
            preferred_contact=FarmerProfile.ContactPreference.PHONE,
            county="Vihiga",
            privacy_consent_at=timezone.now(),
            verification_status=FarmerProfile.VerificationStatus.VERIFIED,
            verification_notes="Synthetic test evidence reviewed.",
        )
        self.invite = BetaInvite.objects.create(
            farmer_profile=self.profile,
            expires_at=timezone.now() + timedelta(days=2),
        )

    def approved_enrollment(self):
        enrollment = BetaEnrollment.objects.create(
            invite=self.invite,
            consent_at=timezone.now(),
            status=BetaEnrollment.Status.APPROVED,
        )
        return enrollment

    def test_plans_are_database_backed_on_public_pricing_and_checkout(self):
        pricing = self.client.get(reverse("pricing"))
        checkout = self.client.get(reverse("checkout"))

        self.assertEqual(pricing.status_code, 200)
        self.assertContains(pricing, "KSh 12,500")
        self.assertContains(pricing, "One advisory session")
        self.assertEqual(checkout.status_code, 200)
        self.assertContains(checkout, "Payments are currently invitation-only")
        self.assertNotContains(checkout, "Debit or credit card")

    def test_invite_requires_consent_and_creates_pending_enrollment(self):
        invite_url = reverse("redeem_beta_invite", args=[self.invite.token])
        response = self.client.post(invite_url, {})

        self.assertEqual(response.status_code, 200)
        self.assertFalse(BetaEnrollment.objects.exists())

        response = self.client.post(invite_url, {"consent": "on"})

        self.assertEqual(response.status_code, 302)
        enrollment = BetaEnrollment.objects.get()
        self.assertEqual(enrollment.status, BetaEnrollment.Status.PENDING)
        self.assertIsNotNone(enrollment.consent_at)
        self.invite.refresh_from_db()
        self.assertIsNotNone(self.invite.redeemed_at)
        self.assertEqual(
            self.client.get(invite_url).status_code,
            410,
        )
        self.assertEqual(
            self.client.get(
                reverse("beta_enrollment", args=[enrollment.access_token])
            ).status_code,
            200,
        )
        self.assertEqual(
            self.client.get(
                reverse("beta_checkout", args=[enrollment.access_token])
            ).status_code,
            403,
        )

    def test_invitation_admin_form_only_offers_verified_profiles(self):
        unverified = FarmerProfile.objects.create(
            registration_type=FarmerProfile.RegistrationType.INDIVIDUAL,
            full_name="Unverified Test Farmer",
            preferred_contact=FarmerProfile.ContactPreference.PHONE,
            county="Vihiga",
            privacy_consent_at=timezone.now(),
        )
        from .admin import BetaInviteAdminForm

        form = BetaInviteAdminForm()

        self.assertTrue(form.fields["farmer_profile"].queryset.filter(pk=self.profile.pk).exists())
        self.assertFalse(form.fields["farmer_profile"].queryset.filter(pk=unverified.pk).exists())

    def test_invitation_model_rejects_unverified_profile(self):
        unverified = FarmerProfile.objects.create(
            registration_type=FarmerProfile.RegistrationType.INDIVIDUAL,
            full_name="Unverified Test Farmer",
            preferred_contact=FarmerProfile.ContactPreference.PHONE,
            county="Vihiga",
            privacy_consent_at=timezone.now(),
        )
        invite = BetaInvite(
            farmer_profile=unverified,
            expires_at=timezone.now() + timedelta(days=1),
        )

        with self.assertRaises(ValidationError):
            invite.full_clean()

    def test_checkout_is_disabled_until_daraja_credentials_are_configured(self):
        enrollment = self.approved_enrollment()

        response = self.client.get(
            reverse("beta_checkout", args=[enrollment.access_token])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "M-PESA checkout is not enabled yet")
        self.assertContains(response, "Payment setup incomplete")

    def test_verified_entrepreneur_can_receive_a_private_beta_invitation(self):
        entrepreneur = PartnerProfile.objects.create(
            applicant_type=PartnerProfile.ApplicantType.BUSINESS,
            contact_name="Test Entrepreneur",
            business_name="Test Agribusiness",
            phone="0712345678",
            preferred_contact=PartnerProfile.ContactPreference.PHONE,
            roles=["supplier"],
            county="Vihiga",
            contact_consent_at=timezone.now(),
            verification_status=PartnerProfile.ReviewStatus.VERIFIED,
            verification_notes="Synthetic business evidence reviewed.",
        )
        invite = BetaInvite.objects.create(
            partner_profile=entrepreneur,
            expires_at=timezone.now() + timedelta(days=2),
        )

        response = self.client.get(reverse("redeem_beta_invite", args=[invite.token]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Agribusiness")

    @override_settings(
        MPESA_CONSUMER_KEY="consumer-key",
        MPESA_CONSUMER_SECRET="consumer-secret",
        MPESA_SHORTCODE="123456",
        MPESA_PASSKEY="passkey",
        MPESA_CALLBACK_URL="https://example.test/portal/payments/mpesa/callback/",
    )
    @patch("farmers.billing.initiate_stk_push")
    def test_approved_beta_member_can_start_stk_payment(self, initiate):
        initiate.return_value = {
            "checkout_request_id": "ws_CO_test_1",
            "merchant_request_id": "merchant_test_1",
            "customer_message": "Prompt sent",
        }
        enrollment = self.approved_enrollment()

        response = self.client.post(
            reverse("beta_checkout", args=[enrollment.access_token]),
            {
                "plan": self.plan.pk,
                "phone_number": "0712345678",
                "payment_consent": "on",
            },
        )

        self.assertEqual(response.status_code, 302)
        payment = MpesaPayment.objects.get()
        self.assertEqual(payment.amount, Decimal("12500"))
        self.assertEqual(payment.phone_number, "254712345678")
        self.assertEqual(payment.status, MpesaPayment.Status.PENDING)
        self.assertEqual(payment.checkout_request_id, "ws_CO_test_1")
        initiate.assert_called_once()

        duplicate = self.client.post(
            reverse("beta_checkout", args=[enrollment.access_token]),
            {
                "plan": self.plan.pk,
                "phone_number": "0712345678",
                "payment_consent": "on",
            },
        )
        self.assertEqual(duplicate.status_code, 200)
        self.assertContains(duplicate, "A payment request is already in progress")
        self.assertEqual(MpesaPayment.objects.count(), 1)
        initiate.assert_called_once()

    @override_settings(
        MPESA_CONSUMER_KEY="consumer-key",
        MPESA_CONSUMER_SECRET="consumer-secret",
        MPESA_SHORTCODE="123456",
        MPESA_PASSKEY="passkey",
        MPESA_CALLBACK_URL="https://example.test/portal/payments/mpesa/callback/",
    )
    @patch("farmers.billing.query_stk_status")
    def test_callback_marks_paid_only_after_query_and_matching_transaction_details(self, query):
        enrollment = self.approved_enrollment()
        payment = MpesaPayment.objects.create(
            enrollment=enrollment,
            plan=self.plan,
            amount=self.plan.price,
            phone_number="254712345678",
            status=MpesaPayment.Status.PENDING,
            checkout_request_id="ws_CO_test_2",
            merchant_request_id="merchant_test_2",
        )
        query.return_value = {"ResponseCode": "0", "ResultCode": "0"}
        callback = {
            "Body": {
                "stkCallback": {
                    "MerchantRequestID": "merchant_test_2",
                    "CheckoutRequestID": "ws_CO_test_2",
                    "ResultCode": 0,
                    "ResultDesc": "The service request is processed successfully.",
                    "CallbackMetadata": {
                        "Item": [
                            {"Name": "Amount", "Value": 12500},
                            {"Name": "MpesaReceiptNumber", "Value": "AB12CD34"},
                            {"Name": "PhoneNumber", "Value": 254712345678},
                        ]
                    },
                }
            }
        }

        response = self.client.post(
            reverse("mpesa_callback"),
            data=json.dumps(callback),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        payment.refresh_from_db()
        self.assertEqual(payment.status, MpesaPayment.Status.PAID)
        self.assertEqual(payment.mpesa_receipt, "AB12CD34")
        self.assertIsNotNone(payment.paid_at)
        query.assert_called_once_with("ws_CO_test_2")

        duplicate = self.client.post(
            reverse("mpesa_callback"),
            data=json.dumps(callback),
            content_type="application/json",
        )
        self.assertEqual(duplicate.status_code, 200)
        self.assertEqual(MpesaPayment.objects.filter(status=MpesaPayment.Status.PAID).count(), 1)

    @override_settings(
        MPESA_CONSUMER_KEY="consumer-key",
        MPESA_CONSUMER_SECRET="consumer-secret",
        MPESA_SHORTCODE="123456",
        MPESA_PASSKEY="passkey",
        MPESA_CALLBACK_URL="https://example.test/portal/payments/mpesa/callback/",
    )
    @patch("farmers.billing.query_stk_status")
    def test_callback_with_mismatched_amount_does_not_mark_payment_paid(self, query):
        enrollment = self.approved_enrollment()
        payment = MpesaPayment.objects.create(
            enrollment=enrollment,
            plan=self.plan,
            amount=self.plan.price,
            phone_number="254712345678",
            status=MpesaPayment.Status.PENDING,
            checkout_request_id="ws_CO_test_3",
            merchant_request_id="merchant_test_3",
        )
        query.return_value = {"ResponseCode": "0", "ResultCode": "0"}
        callback = {
            "Body": {
                "stkCallback": {
                    "MerchantRequestID": "merchant_test_3",
                    "CheckoutRequestID": "ws_CO_test_3",
                    "ResultCode": 0,
                    "CallbackMetadata": {
                        "Item": [
                            {"Name": "Amount", "Value": 100},
                            {"Name": "MpesaReceiptNumber", "Value": "AB12CD99"},
                            {"Name": "PhoneNumber", "Value": 254712345678},
                        ]
                    },
                }
            }
        }

        response = self.client.post(
            reverse("mpesa_callback"),
            data=json.dumps(callback),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        payment.refresh_from_db()
        self.assertEqual(payment.status, MpesaPayment.Status.PENDING)
        self.assertIsNone(payment.mpesa_receipt)

    def test_phone_number_validation_accepts_kenyan_mobile_formats_only(self):
        self.assertEqual(normalize_phone_number("+254 712 345 678"), "254712345678")
        self.assertEqual(normalize_phone_number("0712345678"), "254712345678")
        with self.assertRaises(MpesaError):
            normalize_phone_number("123456")

    def test_plan_prices_must_be_whole_positive_kes_amounts(self):
        plan = ServicePlan(
            slug="fractional-plan",
            name="Fractional",
            price=Decimal("100.50"),
            tagline="Test",
            description="Test",
        )
        with self.assertRaises(ValidationError):
            plan.full_clean()

    def test_profile_retention_detaches_and_anonymizes_private_beta_payments(self):
        enrollment = self.approved_enrollment()
        payment = MpesaPayment.objects.create(
            enrollment=enrollment,
            plan=self.plan,
            amount=self.plan.price,
            phone_number="254712345678",
            status=MpesaPayment.Status.PENDING,
            checkout_request_id="ws_CO_retention",
            merchant_request_id="merchant_retention",
        )

        self.profile.delete()

        payment.refresh_from_db()
        self.assertIsNone(payment.enrollment)
        self.assertEqual(payment.status, MpesaPayment.Status.FAILED)
        self.assertEqual(payment.phone_number, "ending 5678")


class MpesaApiRequestTests(TestCase):
    @override_settings(
        DEBUG=False,
        MPESA_ENVIRONMENT="production",
        MPESA_BASE_URL="https://api.safaricom.co.ke",
        MPESA_CONSUMER_KEY="consumer-key",
        MPESA_CONSUMER_SECRET="consumer-secret",
        MPESA_SHORTCODE="123456",
        MPESA_PASSKEY="passkey",
        MPESA_CALLBACK_URL="https://example.test/portal/payments/mpesa/callback/",
        MPESA_TRANSACTION_TYPE="CustomerPayBillOnline",
    )
    @patch("farmers.mpesa.urlopen")
    def test_stk_push_authenticates_and_sends_expected_transaction(self, urlopen):
        from .mpesa import initiate_stk_push

        responses = [
            {"access_token": "access-token"},
            {
                "ResponseCode": "0",
                "CheckoutRequestID": "ws_CO_test",
                "MerchantRequestID": "merchant_test",
                "CustomerMessage": "Prompt sent",
            },
        ]
        fake_responses = []
        for payload in responses:
            response = MagicMock()
            response.__enter__.return_value.read.return_value = json.dumps(payload).encode()
            fake_responses.append(response)
        urlopen.side_effect = fake_responses

        result = initiate_stk_push(
            phone_number="0712345678",
            amount=Decimal("12500"),
            account_reference="MF100",
            description="Growth",
        )

        self.assertEqual(result["checkout_request_id"], "ws_CO_test")
        self.assertEqual(urlopen.call_count, 2)
        stk_request = urlopen.call_args_list[1].args[0]
        payload = json.loads(stk_request.data)
        self.assertEqual(payload["Amount"], 12500)
        self.assertEqual(payload["PhoneNumber"], "254712345678")
        self.assertEqual(payload["CallBackURL"], "https://example.test/portal/payments/mpesa/callback/")
        self.assertEqual(stk_request.get_header("Authorization"), "Bearer access-token")

    @override_settings(
        MPESA_CONSUMER_KEY="",
        MPESA_CONSUMER_SECRET="",
        MPESA_SHORTCODE="",
        MPESA_PASSKEY="",
        MPESA_CALLBACK_URL="",
    )
    @patch("farmers.mpesa.urlopen")
    def test_missing_merchant_credentials_fail_without_network_request(self, urlopen):
        from .mpesa import initiate_stk_push

        with self.assertRaises(MpesaError):
            initiate_stk_push(
                phone_number="0712345678",
                amount=Decimal("12500"),
                account_reference="MF100",
                description="Growth",
            )
        urlopen.assert_not_called()
