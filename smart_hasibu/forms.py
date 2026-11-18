from decimal import Decimal
from django.utils import timezone

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db.models import F, Sum
from django.db.models.functions import Coalesce

from farmers.templatetags.custom_i18n import localize_choices, translate
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
            "I agree to create a private SmartHasibu account. My records are visible "
            "to me and authorised support staff only."
        )
    )

    def __init__(self, *args, lang="en", **kwargs):
        super().__init__(*args, **kwargs)
        self.lang = lang
        self.fields["name"].label = translate("field.your_name", lang)
        self.fields["password1"].label = translate("field.password", lang)
        self.fields["password1"].help_text = translate("help.password_unique", lang)
        self.fields["password2"].label = translate("field.confirm_password", lang)
        self.fields["consent"].label = translate("field.consent_smarthasibu", lang)

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        user_model = get_user_model()
        if user_model.objects.filter(email__iexact=email).exists():
            raise ValidationError(translate("err.email_taken", self.lang))
        return email

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            self.add_error("password2", translate("err.passwords_mismatch", self.lang))
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

    def __init__(self, *args, lang="en", **kwargs):
        super().__init__(*args, **kwargs)
        self.lang = lang
        self.fields["name"].label = translate("field.enterprise_name", lang)
        self.fields["name"].help_text = translate("help.enterprise_name_examples", lang)
        self.fields["category"].label = translate("field.enterprise_category", lang)
        self.fields["category"].choices = localize_choices(
            FarmEnterprise.Category.choices, lang, "choice.enterprise_category"
        )


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

    def __init__(self, *args, user, lang="en", **kwargs):
        super().__init__(*args, **kwargs)
        self.lang = lang
        self.fields["enterprise"].queryset = FarmEnterprise.objects.filter(owner=user)
        self.fields["enterprise"].label = translate("field.ledger_enterprise", lang)
        self.fields["entry_type"].label = translate("field.entry_type", lang)
        self.fields["entry_type"].choices = localize_choices(
            LedgerEntry.EntryType.choices, lang, "choice.entry_type"
        )
        self.fields["category"].label = translate("field.ledger_category", lang)
        self.fields["category"].choices = localize_choices(
            LedgerEntry.Category.choices, lang, "choice.ledger_category"
        )
        self.fields["amount"].label = translate("field.amount", lang)
        self.fields["amount"].help_text = translate("help.amount_full", lang)
        self.fields["occurred_on"].label = translate("field.occurred_on", lang)
        self.fields["description"].label = translate("field.description", lang)
        self.fields["counterparty"].label = translate("field.counterparty", lang)
        self.fields["counterparty"].help_text = translate("help.counterparty", lang)
        self.fields["is_credit"].label = translate("field.is_credit", lang)
        self.fields["is_credit"].help_text = translate("help.is_credit", lang)

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
            self.add_error("category", translate("err.category_mismatch", self.lang))
        amount = cleaned_data.get("amount")
        if amount is not None and self.instance.pk:
            settled = self.instance.amount_settled
            if amount < settled:
                self.add_error(
                    "amount",
                    translate("err.amount_below_settled", self.lang, amount="%.2f" % settled),
                )
        return cleaned_data


class CreditSettlementForm(forms.ModelForm):
    class Meta:
        model = CreditSettlement
        fields = ["entry", "amount", "settled_on", "note"]
        widgets = {
            "settled_on": forms.DateInput(attrs={"type": "date"}),
            "amount": forms.NumberInput(attrs={"min": "0.01", "step": "0.01", "inputmode": "decimal"}),
        }

    def __init__(self, *args, user, lang="en", **kwargs):
        super().__init__(*args, **kwargs)
        self.lang = lang
        self.fields["entry"].queryset = (
            LedgerEntry.objects.filter(enterprise__owner=user, is_credit=True)
            .annotate(
                settled=Coalesce(Sum("settlements__amount"), Decimal("0.00"))
            )
            .filter(amount__gt=F("settled"))
            .select_related("enterprise")
        )
        self.fields["entry"].label = translate("field.settlement_entry", lang)
        entry_type_labels = dict(
            localize_choices(LedgerEntry.EntryType.choices, lang, "choice.entry_type")
        )
        self.fields["entry"].label_from_instance = lambda entry: (
            f"{entry_type_labels.get(entry.entry_type, entry.entry_type)} — {entry.description} "
            f"({entry.enterprise.name}, KSh {entry.amount - entry.settled} outstanding)"
        )
        self.fields["amount"].label = translate("field.amount", lang)
        self.fields["settled_on"].label = translate("field.settled_on", lang)
        self.fields["note"].label = translate("field.note", lang)
