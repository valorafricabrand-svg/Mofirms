from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from .models import CreditSettlement, FarmEnterprise, LedgerEntry
from .models import SmartHasibuAccount


class SmartHasibuTests(TestCase):
    def setUp(self):
        self.signup_url = reverse("smart_hasibu:signup")
        self.dashboard_url = reverse("smart_hasibu:dashboard")
        self.user = get_user_model().objects.create_user(
            username="farmer@example.test",
            email="farmer@example.test",
            password="Synthetic-Only-Password-123!",
            first_name="Synthetic Farmer",
        )
        self.enterprise = FarmEnterprise.objects.create(
            owner=self.user,
            name="Synthetic Tomato Plot",
            category=FarmEnterprise.Category.CROPS,
        )

    def post_entry(
        self,
        *,
        enterprise=None,
        entry_type=LedgerEntry.EntryType.INCOME,
        category="sales",
        amount="1250.00",
        is_credit="",
    ):
        return self.client.post(
            self.dashboard_url,
            {
                "action": "entry",
                "enterprise": enterprise or self.enterprise.pk,
                "entry_type": entry_type,
                "category": category,
                "amount": amount,
                "occurred_on": date.today().isoformat(),
                "description": "Synthetic tomato sale",
                "counterparty": "Synthetic market buyer",
                "is_credit": is_credit,
            },
        )

    def test_signup_creates_private_account_and_authenticates(self):
        response = self.client.post(
            self.signup_url,
            {
                "name": "New Synthetic Farmer",
                "email": "newfarmer@example.test",
                "password1": "Pilot-Only-Password-832!",
                "password2": "Pilot-Only-Password-832!",
                "consent": "on",
            },
        )

        self.assertRedirects(response, self.dashboard_url)
        user = get_user_model().objects.get(email="newfarmer@example.test")
        self.assertTrue(user.is_authenticated)
        self.assertEqual(self.client.session["_auth_user_id"], str(user.pk))
        self.assertEqual(FarmEnterprise.objects.filter(owner=user).count(), 0)
        self.assertIsNotNone(user.smart_hasibu_account.consent_at)

    def test_dashboard_requires_login_and_displays_only_owned_entries(self):
        self.assertRedirects(self.client.get(self.dashboard_url), f"{reverse('smart_hasibu:login')}?next={self.dashboard_url}")
        LedgerEntry.objects.create(
            enterprise=self.enterprise,
            entry_type=LedgerEntry.EntryType.INCOME,
            category="sales",
            amount="2500.00",
            description="Synthetic sale",
        )
        other_user = get_user_model().objects.create_user(
            username="another@example.test",
            email="another@example.test",
            password="Synthetic-Only-Password-123!",
        )
        other_enterprise = FarmEnterprise.objects.create(
            owner=other_user,
            name="Other private farm",
            category=FarmEnterprise.Category.LIVESTOCK,
        )
        self.client.force_login(self.user)

        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "KSh 2,500.00")
        self.assertNotContains(response, "Other private farm")
        self.assertEqual(
            self.client.get(f"{self.dashboard_url}?enterprise={other_enterprise.pk}").status_code,
            404,
        )

    def test_foreign_enterprise_cannot_be_used_for_transaction(self):
        other_user = get_user_model().objects.create_user(
            username="other-owner@example.test",
            email="other-owner@example.test",
            password="Synthetic-Only-Password-123!",
        )
        other_enterprise = FarmEnterprise.objects.create(
            owner=other_user,
            name="Private other enterprise",
            category=FarmEnterprise.Category.CROPS,
        )
        self.client.force_login(self.user)

        response = self.post_entry(enterprise=other_enterprise.pk)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(LedgerEntry.objects.count(), 0)

    def test_credit_sale_and_partial_payments_do_not_double_count_income(self):
        self.client.force_login(self.user)
        response = self.post_entry(amount="1000.00", is_credit="on")
        self.assertRedirects(response, self.dashboard_url)
        entry = LedgerEntry.objects.get()
        self.assertEqual(entry.amount_outstanding, Decimal("1000.00"))

        response = self.client.post(
            self.dashboard_url,
            {
                "action": "settlement",
                "entry": entry.pk,
                "amount": "400.00",
                "settled_on": date.today().isoformat(),
                "note": "Synthetic part payment",
            },
        )
        self.assertRedirects(response, self.dashboard_url)
        entry.refresh_from_db()
        self.assertEqual(entry.amount_outstanding, Decimal("600.00"))

        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["income_total"], Decimal("1000.00"))
        self.assertEqual(response.context["receivable_total"], Decimal("600.00"))

    def test_overpayment_and_wrong_category_are_rejected(self):
        self.client.force_login(self.user)
        self.post_entry(entry_type=LedgerEntry.EntryType.INCOME, category="inputs")
        self.assertEqual(LedgerEntry.objects.count(), 0)

        entry = LedgerEntry.objects.create(
            enterprise=self.enterprise,
            entry_type=LedgerEntry.EntryType.INCOME,
            category="sales",
            amount="500.00",
            description="Synthetic credit sale",
            is_credit=True,
        )
        response = self.client.post(
            self.dashboard_url,
            {
                "action": "settlement",
                "entry": entry.pk,
                "amount": "501.00",
                "settled_on": date.today().isoformat(),
                "note": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(CreditSettlement.objects.count(), 0)
        entry.refresh_from_db()
        self.assertEqual(entry.amount_outstanding, Decimal("500.00"))

    def test_expense_and_income_categories_are_validated_in_model(self):
        entry = LedgerEntry(
            enterprise=self.enterprise,
            entry_type=LedgerEntry.EntryType.EXPENSE,
            category="sales",
            amount="10.00",
            description="Synthetic invalid category",
        )
        with self.assertRaises(ValidationError):
            entry.full_clean()
