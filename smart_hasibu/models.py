from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.utils import timezone


class SmartHasibuAccount(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="smart_hasibu_account",
    )
    consent_at = models.DateTimeField()
    privacy_policy_version = models.CharField(max_length=24, default="pilot-2026-11-02")
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    def __str__(self):
        return f"SmartHasibu account for {self.user_id}"


class FarmEnterprise(models.Model):
    class Category(models.TextChoices):
        CROPS = "crops", "Crops and horticulture"
        LIVESTOCK = "livestock", "Livestock and dairy"
        POULTRY = "poultry", "Poultry"
        PRODUCE_TRADE = "produce_trade", "Produce buying or selling"
        FARM_SERVICES = "farm_services", "Farm services or inputs"
        OTHER = "other", "Other"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="smart_hasibu_enterprises",
    )
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=24, choices=Category.choices)
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        ordering = ["name", "pk"]
        constraints = [
            models.UniqueConstraint(fields=["owner", "name"], name="unique_owner_enterprise_name")
        ]

    def __str__(self):
        return self.name


class LedgerEntry(models.Model):
    class EntryType(models.TextChoices):
        INCOME = "income", "Money earned or sale"
        EXPENSE = "expense", "Money spent or cost"

    class Category(models.TextChoices):
        SALES = "sales", "Produce or product sales"
        LIVESTOCK = "livestock", "Livestock or animal products"
        SERVICES = "services", "Service income"
        OTHER_INCOME = "other_income", "Other income"
        INPUTS = "inputs", "Seeds, feed, or other inputs"
        LABOUR = "labour", "Labour"
        TRANSPORT = "transport", "Transport"
        STORAGE = "storage", "Storage or packaging"
        UTILITIES = "utilities", "Water, power, or fuel"
        EQUIPMENT = "equipment", "Tools or equipment"
        OTHER_EXPENSE = "other_expense", "Other expense"

    enterprise = models.ForeignKey(
        FarmEnterprise,
        on_delete=models.CASCADE,
        related_name="entries",
    )
    entry_type = models.CharField(max_length=8, choices=EntryType.choices)
    category = models.CharField(max_length=20, choices=Category.choices)
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    occurred_on = models.DateField(default=timezone.localdate)
    description = models.CharField(max_length=180)
    counterparty = models.CharField(
        max_length=100,
        blank=True,
        help_text="Optional customer or supplier name, visible only in your account.",
    )
    is_credit = models.BooleanField(
        default=False,
        help_text="Tick if the full amount has not yet been paid.",
    )
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        ordering = ["-occurred_on", "-created_at"]
        indexes = [
            models.Index(fields=["enterprise", "occurred_on"]),
            models.Index(fields=["enterprise", "entry_type", "is_credit"]),
        ]

    def __str__(self):
        return f"{self.get_entry_type_display()}: KSh {self.amount} ({self.enterprise})"

    def clean(self):
        super().clean()
        if self.entry_type == self.EntryType.INCOME and self.category not in {
            "sales", "livestock", "services", "other_income"
        }:
            raise ValidationError({"category": "Choose an income category."})
        if self.entry_type == self.EntryType.EXPENSE and self.category not in {
            "inputs", "labour", "transport", "storage", "utilities",
            "equipment", "other_expense"
        }:
            raise ValidationError({"category": "Choose an expense category."})

    @property
    def amount_settled(self):
        if not self.pk:
            return Decimal("0.00")
        if hasattr(self, "settled"):
            return self.settled
        return self.settlements.aggregate(
            total=Coalesce(Sum("amount"), Decimal("0.00"))
        )["total"]

    @property
    def amount_outstanding(self):
        return max(self.amount - self.amount_settled, Decimal("0.00"))


class CreditSettlement(models.Model):
    entry = models.ForeignKey(
        LedgerEntry,
        on_delete=models.CASCADE,
        related_name="settlements",
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    settled_on = models.DateField(default=timezone.localdate)
    note = models.CharField(max_length=160, blank=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        ordering = ["-settled_on", "-created_at"]

    def __str__(self):
        return f"KSh {self.amount} settlement — {self.entry_id}"

    def clean(self):
        super().clean()
        if self.entry_id and not self.entry.is_credit:
            raise ValidationError({"entry": "Payments can only be recorded against a credit entry."})
        if self.entry_id and self.amount:
            previous = self.entry.settlements.exclude(pk=self.pk).aggregate(
                total=Coalesce(Sum("amount"), Decimal("0.00"))
            )["total"]
            if previous + self.amount > self.entry.amount:
                raise ValidationError({"amount": "The payment is greater than the outstanding balance."})
