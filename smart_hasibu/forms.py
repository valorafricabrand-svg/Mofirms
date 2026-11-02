from decimal import Decimal
from django.utils import timezone

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db.models import F, Sum
from django.db.models.functions import Coalesce

from .models import CreditSettlement, FarmEnterprise, LedgerEntry, SmartHasibuAccount


class FarmerSignupForm(forms.Form):
    name = forms.CharField(max_length=150, label="Your name")
    email = forms.EmailField()
    password1 = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput,
        help_text="Choose a unique password. Never reuse your mobile-money PIN.",
    )
    password2 = forms.CharField(
        label="Confirm password",
        strip=False,
        widget=forms.PasswordInput,
    )
    consent = forms.BooleanField(
        label=(
            "I agree to create a private SmartHasibu pilot account. My records are visible "
            "to me and authorised support staff only."
        )
    )

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        user_model = get_user_model()
        if user_model.objects.filter(email__iexact=email).exists():
            raise ValidationError("An account already uses this email address.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            self.add_error("password2", "The passwords do not match.")
        if password1 and cleaned_data.get("email"):
            candidate = get_user_model()(username=cleaned_data["email"], email=cleaned_data["email"])
            try:
                validate_password(password1, candidate)
            except ValidationError as error:
                self.add_error("password1", error)
        return cleaned_data

    def save(self):
        user_model = get_user_model()
        email = self.cleaned_data["email"]
        user = user_model(
            username=email,
            email=email,
            first_name=self.cleaned_data["name"].strip(),
        )
        user.set_password(self.cleaned_data["password1"])
        user.save()
        SmartHasibuAccount.objects.create(user=user, consent_at=timezone.now())
        return user


class FarmEnterpriseForm(forms.ModelForm):
    class Meta:
        model = FarmEnterprise
        fields = ["name", "category"]
        help_texts = {
            "name": "Examples: Greenhouse tomatoes, dairy goats, or maize plot.",
        }


class LedgerEntryForm(forms.ModelForm):
    class Meta:
        model = LedgerEntry
        fields = [
            "enterprise",
            "entry_type",
            "category",
            "amount",
            "occurred_on",
            "description",
            "counterparty",
            "is_credit",
        ]
        widgets = {
            "occurred_on": forms.DateInput(attrs={"type": "date"}),
            "amount": forms.NumberInput(attrs={"min": "0.01", "step": "0.01", "inputmode": "decimal"}),
        }
        help_texts = {
            "amount": "Enter the full sale or expense amount in Kenyan shillings.",
            "is_credit": "Tick when some or all of this sale or expense is still unpaid.",
        }

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["enterprise"].queryset = FarmEnterprise.objects.filter(owner=user)

    def clean(self):
        cleaned_data = super().clean()
        entry_type = cleaned_data.get("entry_type")
        category = cleaned_data.get("category")
        allowed = {
            LedgerEntry.EntryType.INCOME: {
                "sales", "livestock", "services", "other_income"
            },
            LedgerEntry.EntryType.EXPENSE: {
                "inputs", "labour", "transport", "storage", "utilities",
                "equipment", "other_expense"
            },
        }
        if entry_type and category and category not in allowed.get(entry_type, set()):
            self.add_error("category", "Choose a category matching income or expense.")
        return cleaned_data


class CreditSettlementForm(forms.ModelForm):
    class Meta:
        model = CreditSettlement
        fields = ["entry", "amount", "settled_on", "note"]
        widgets = {
            "settled_on": forms.DateInput(attrs={"type": "date"}),
            "amount": forms.NumberInput(attrs={"min": "0.01", "step": "0.01", "inputmode": "decimal"}),
        }

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["entry"].queryset = (
            LedgerEntry.objects.filter(enterprise__owner=user, is_credit=True)
            .annotate(
                settled=Coalesce(Sum("settlements__amount"), Decimal("0.00"))
            )
            .filter(amount__gt=F("settled"))
            .select_related("enterprise")
        )
        self.fields["entry"].label_from_instance = lambda entry: (
            f"{entry.get_entry_type_display()} — {entry.description} "
            f"({entry.enterprise.name}, KSh {entry.amount - entry.settled} outstanding)"
        )
