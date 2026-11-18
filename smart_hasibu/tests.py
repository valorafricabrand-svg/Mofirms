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

    def test_owner_can_edit_their_own_entry(self):
        self.client.force_login(self.user)
        entry = LedgerEntry.objects.create(
            enterprise=self.enterprise,
            entry_type=LedgerEntry.EntryType.INCOME,
            category="sales",
            amount="100.00",
            description="Synthetic original sale",
        )

        response = self.client.post(
            reverse("smart_hasibu:entry_edit", args=[entry.pk]),
            {
                "enterprise": self.enterprise.pk,
                "entry_type": LedgerEntry.EntryType.INCOME,
                "category": "sales",
                "amount": "150.00",
                "occurred_on": date.today().isoformat(),
                "description": "Synthetic updated sale",
                "counterparty": "",
                "is_credit": "",
            },
        )

        self.assertRedirects(response, self.dashboard_url)
        entry.refresh_from_db()
        self.assertEqual(entry.amount, Decimal("150.00"))
        self.assertEqual(entry.description, "Synthetic updated sale")

    def test_cannot_edit_entry_below_amount_already_settled(self):
        self.client.force_login(self.user)
        entry = LedgerEntry.objects.create(
            enterprise=self.enterprise,
            entry_type=LedgerEntry.EntryType.INCOME,
            category="sales",
            amount="500.00",
            description="Synthetic credit sale",
            is_credit=True,
        )
        CreditSettlement.objects.create(entry=entry, amount="300.00")

        response = self.client.post(
            reverse("smart_hasibu:entry_edit", args=[entry.pk]),
            {
                "enterprise": self.enterprise.pk,
                "entry_type": LedgerEntry.EntryType.INCOME,
                "category": "sales",
                "amount": "200.00",
                "occurred_on": date.today().isoformat(),
                "description": "Synthetic credit sale",
                "counterparty": "",
                "is_credit": "on",
            },
        )

        self.assertEqual(response.status_code, 200)
        entry.refresh_from_db()
        self.assertEqual(entry.amount, Decimal("500.00"))

    def test_owner_cannot_edit_or_delete_another_users_entry(self):
        other_user = get_user_model().objects.create_user(
            username="owner-two@example.test",
            email="owner-two@example.test",
            password="Synthetic-Only-Password-123!",
        )
        other_enterprise = FarmEnterprise.objects.create(
            owner=other_user,
            name="Other owner enterprise",
            category=FarmEnterprise.Category.CROPS,
        )
        other_entry = LedgerEntry.objects.create(
            enterprise=other_enterprise,
            entry_type=LedgerEntry.EntryType.INCOME,
            category="sales",
            amount="100.00",
            description="Synthetic other sale",
        )
        self.client.force_login(self.user)

        self.assertEqual(
            self.client.get(
                reverse("smart_hasibu:entry_edit", args=[other_entry.pk])
            ).status_code,
            404,
        )
        self.assertEqual(
            self.client.post(
                reverse("smart_hasibu:entry_delete", args=[other_entry.pk])
            ).status_code,
            404,
        )
        self.assertTrue(LedgerEntry.objects.filter(pk=other_entry.pk).exists())

    def test_owner_can_delete_their_own_entry(self):
        self.client.force_login(self.user)
        entry = LedgerEntry.objects.create(
            enterprise=self.enterprise,
            entry_type=LedgerEntry.EntryType.EXPENSE,
            category="inputs",
            amount="75.00",
            description="Synthetic input cost",
        )

        response = self.client.post(
            reverse("smart_hasibu:entry_delete", args=[entry.pk])
        )

        self.assertRedirects(response, self.dashboard_url)
        entry.refresh_from_db()
        self.assertTrue(entry.is_deleted)
        self.assertIsNotNone(entry.deleted_at)

    def test_deleted_entry_is_hidden_but_restorable(self):
        self.client.force_login(self.user)
        entry = LedgerEntry.objects.create(
            enterprise=self.enterprise,
            entry_type=LedgerEntry.EntryType.EXPENSE,
            category="inputs",
            amount="75.00",
            description="Synthetic restorable cost",
        )
        self.client.post(reverse("smart_hasibu:entry_delete", args=[entry.pk]))

        dashboard_response = self.client.get(self.dashboard_url)
        self.assertEqual(len(dashboard_response.context["entries"]), 0)
        self.assertEqual(len(dashboard_response.context["deleted_entries"]), 1)
        self.assertEqual(
            dashboard_response.context["deleted_entries"][0].description,
            "Synthetic restorable cost",
        )
        self.assertEqual(dashboard_response.context["income_total"], Decimal("0.00"))

        self.assertEqual(
            self.client.get(
                reverse("smart_hasibu:entry_edit", args=[entry.pk])
            ).status_code,
            404,
        )

        restore_response = self.client.post(
            reverse("smart_hasibu:entry_restore", args=[entry.pk])
        )
        self.assertRedirects(restore_response, self.dashboard_url)
        entry.refresh_from_db()
        self.assertFalse(entry.is_deleted)
        self.assertIsNone(entry.deleted_at)
        self.assertContains(self.client.get(self.dashboard_url), "Synthetic restorable cost")

    def test_cannot_restore_another_users_deleted_entry(self):
        other_user = get_user_model().objects.create_user(
            username="restore-other@example.test",
            email="restore-other@example.test",
            password="Synthetic-Only-Password-123!",
        )
        other_enterprise = FarmEnterprise.objects.create(
            owner=other_user,
            name="Other restorer enterprise",
            category=FarmEnterprise.Category.CROPS,
        )
        other_entry = LedgerEntry.objects.create(
            enterprise=other_enterprise,
            entry_type=LedgerEntry.EntryType.INCOME,
            category="sales",
            amount="100.00",
            description="Synthetic other deleted sale",
            is_deleted=True,
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("smart_hasibu:entry_restore", args=[other_entry.pk])
        )
        self.assertEqual(response.status_code, 404)

    def test_enterprise_rename(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("smart_hasibu:enterprise_edit", args=[self.enterprise.pk]),
            {"name": "Renamed Tomato Plot", "category": FarmEnterprise.Category.CROPS},
        )

        self.assertRedirects(response, self.dashboard_url)
        self.enterprise.refresh_from_db()
        self.assertEqual(self.enterprise.name, "Renamed Tomato Plot")

    def test_enterprise_with_entries_cannot_be_deleted(self):
        self.client.force_login(self.user)
        LedgerEntry.objects.create(
            enterprise=self.enterprise,
            entry_type=LedgerEntry.EntryType.INCOME,
            category="sales",
            amount="50.00",
            description="Synthetic sale",
        )

        response = self.client.post(
            reverse("smart_hasibu:enterprise_delete", args=[self.enterprise.pk])
        )

        self.assertRedirects(response, self.dashboard_url)
        self.assertTrue(FarmEnterprise.objects.filter(pk=self.enterprise.pk).exists())

    def test_empty_enterprise_can_be_deleted(self):
        self.client.force_login(self.user)
        empty_enterprise = FarmEnterprise.objects.create(
            owner=self.user,
            name="Synthetic Empty Enterprise",
            category=FarmEnterprise.Category.OTHER,
        )

        response = self.client.post(
            reverse("smart_hasibu:enterprise_delete", args=[empty_enterprise.pk])
        )

        self.assertRedirects(response, self.dashboard_url)
        self.assertFalse(FarmEnterprise.objects.filter(pk=empty_enterprise.pk).exists())

    def test_export_entries_returns_csv_for_owned_records_only(self):
        self.client.force_login(self.user)
        LedgerEntry.objects.create(
            enterprise=self.enterprise,
            entry_type=LedgerEntry.EntryType.INCOME,
            category="sales",
            amount="321.00",
            description="Synthetic export sale",
            occurred_on=date.today(),
        )

        response = self.client.get(
            reverse("smart_hasibu:export_entries"),
            {"month": date.today().strftime("%Y-%m")},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")
        content = response.content.decode()
        self.assertIn("Synthetic export sale", content)
        self.assertIn("321.00", content)

    def test_category_filter_narrows_entries_and_summary(self):
        self.client.force_login(self.user)
        LedgerEntry.objects.create(
            enterprise=self.enterprise,
            entry_type=LedgerEntry.EntryType.INCOME,
            category="sales",
            amount="200.00",
            description="Synthetic produce sale",
        )
        LedgerEntry.objects.create(
            enterprise=self.enterprise,
            entry_type=LedgerEntry.EntryType.EXPENSE,
            category="inputs",
            amount="50.00",
            description="Synthetic seed cost",
        )

        response = self.client.get(self.dashboard_url, {"category": "inputs"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Synthetic seed cost")
        self.assertNotContains(response, "Synthetic produce sale")
        self.assertEqual(response.context["expense_total"], Decimal("50.00"))
        self.assertEqual(response.context["income_total"], Decimal("0.00"))

        invalid_response = self.client.get(self.dashboard_url, {"category": "not-a-category"})
        self.assertEqual(invalid_response.status_code, 400)

    def test_search_filters_by_description_and_counterparty(self):
        self.client.force_login(self.user)
        LedgerEntry.objects.create(
            enterprise=self.enterprise,
            entry_type=LedgerEntry.EntryType.INCOME,
            category="sales",
            amount="300.00",
            description="Synthetic maize sale",
            counterparty="Synthetic Buyer Co",
        )
        LedgerEntry.objects.create(
            enterprise=self.enterprise,
            entry_type=LedgerEntry.EntryType.INCOME,
            category="sales",
            amount="150.00",
            description="Synthetic bean sale",
            counterparty="Different Trader",
        )

        by_description = self.client.get(self.dashboard_url, {"q": "maize"})
        self.assertContains(by_description, "Synthetic maize sale")
        self.assertNotContains(by_description, "Synthetic bean sale")

        by_counterparty = self.client.get(self.dashboard_url, {"q": "Buyer Co"})
        self.assertContains(by_counterparty, "Synthetic maize sale")
        self.assertNotContains(by_counterparty, "Synthetic bean sale")

    def test_category_and_enterprise_breakdown_totals(self):
        self.client.force_login(self.user)
        second_enterprise = FarmEnterprise.objects.create(
            owner=self.user,
            name="Synthetic Second Enterprise",
            category=FarmEnterprise.Category.LIVESTOCK,
        )
        LedgerEntry.objects.create(
            enterprise=self.enterprise,
            entry_type=LedgerEntry.EntryType.INCOME,
            category="sales",
            amount="100.00",
            description="Synthetic sale one",
        )
        LedgerEntry.objects.create(
            enterprise=self.enterprise,
            entry_type=LedgerEntry.EntryType.INCOME,
            category="sales",
            amount="50.00",
            description="Synthetic sale two",
        )
        LedgerEntry.objects.create(
            enterprise=second_enterprise,
            entry_type=LedgerEntry.EntryType.EXPENSE,
            category="inputs",
            amount="40.00",
            description="Synthetic input cost",
        )

        response = self.client.get(self.dashboard_url)

        category_rows = {
            (row["entry_type"], row["category"]): row["total"]
            for row in response.context["category_breakdown"]
        }
        self.assertEqual(category_rows[(LedgerEntry.EntryType.INCOME, "sales")], Decimal("150.00"))
        self.assertEqual(category_rows[(LedgerEntry.EntryType.EXPENSE, "inputs")], Decimal("40.00"))

        enterprise_rows = {
            row["enterprise__name"]: row for row in response.context["enterprise_breakdown"]
        }
        self.assertEqual(enterprise_rows["Synthetic Tomato Plot"]["income"], Decimal("150.00"))
        self.assertEqual(enterprise_rows["Synthetic Second Enterprise"]["expenses"], Decimal("40.00"))
        self.assertEqual(enterprise_rows["Synthetic Second Enterprise"]["net"], Decimal("-40.00"))

    def test_dashboard_paginates_beyond_fifty_entries(self):
        self.client.force_login(self.user)
        LedgerEntry.objects.bulk_create(
            [
                LedgerEntry(
                    enterprise=self.enterprise,
                    entry_type=LedgerEntry.EntryType.INCOME,
                    category="sales",
                    amount="10.00",
                    description=f"Synthetic bulk sale {i}",
                )
                for i in range(60)
            ]
        )

        first_page = self.client.get(self.dashboard_url)
        second_page = self.client.get(self.dashboard_url, {"page": 2})

        self.assertEqual(len(first_page.context["entries"]), 50)
        self.assertEqual(len(second_page.context["entries"]), 10)
