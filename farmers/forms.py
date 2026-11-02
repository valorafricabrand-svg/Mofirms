from io import BytesIO
import logging
from pathlib import Path
import subprocess
import uuid

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.forms import formset_factory
from PIL import Image, ImageOps, UnidentifiedImageError

from .models import (
    ACTIVITY_CHOICES,
    COUNTIES,
    PARTNER_DELIVERY_CHOICES,
    PARTNER_OFFER_CHOICES,
    PARTNER_ROLE_CHOICES,
    PRODUCE_CATEGORY_CHOICES,
    SUPPORT_CHOICES,
    FarmerDocument,
    FarmerProfile,
    FinancialAnalysisDocument,
    FinancialAnalysisRequest,
    PartnerDocument,
    PartnerProfile,
)


logger = logging.getLogger(__name__)


MAX_DOCUMENT_SIZE = 5 * 1024 * 1024
MAX_DOCUMENTS_PER_REGISTRATION = 20
Image.MAX_IMAGE_PIXELS = 20_000_000


class FarmerRegistrationForm(forms.ModelForm):
    activities = forms.MultipleChoiceField(
        choices=ACTIVITY_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="What do you farm or plan to farm?",
    )
    water_sources = forms.MultipleChoiceField(
        choices=FarmerProfile.WaterSource.choices,
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Water sources used",
    )
    sales_channels = forms.MultipleChoiceField(
        choices=[
            ("farm_gate", "Farm-gate sales"),
            ("local_market", "Local market"),
            ("trader", "Trader or broker"),
            ("cooperative", "Cooperative or farmer group"),
            ("processor", "Processor"),
            ("retail", "Retail or direct to consumers"),
            ("contract", "Contract or institutional buyer"),
            ("other", "Other"),
        ],
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Where do you currently sell?",
    )
    challenges = forms.MultipleChoiceField(
        choices=[
            ("inputs", "Input cost or availability"),
            ("water", "Water or irrigation"),
            ("weather", "Weather, pests, or disease"),
            ("labour", "Labour or skills"),
            ("storage", "Storage or post-harvest losses"),
            ("transport", "Transport or logistics"),
            ("markets", "Finding reliable buyers"),
            ("finance", "Access to finance"),
            ("records", "Business records or planning"),
            ("other", "Other"),
        ],
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="What are your main farming or business challenges?",
    )
    support_interests = forms.MultipleChoiceField(
        choices=SUPPORT_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="What support would be most useful?",
    )
    privacy_consent = forms.BooleanField(
        required=True,
        label="I agree that MoFirms may use these details to review this registration and contact me about it.",
    )
    website = forms.CharField(required=False, widget=forms.HiddenInput)
    group_authorization_confirmed = forms.BooleanField(
        required=False,
        label="I am authorised to submit information for this group and have informed its members.",
    )

    class Meta:
        model = FarmerProfile
        fields = [
            "registration_type",
            "privacy_consent",
            "group_authorization_confirmed",
            "website",
            "full_name",
            "phone",
            "email",
            "preferred_contact",
            "preferred_language",
            "group_name",
            "group_type",
            "group_registration_status",
            "group_registration_number",
            "group_member_count",
            "representative_role",
            "county",
            "sub_county",
            "ward",
            "local_area",
            "activities",
            "main_products",
            "farm_size",
            "farm_size_unit",
            "land_access",
            "years_farming",
            "water_sources",
            "production_summary",
            "sales_band",
            "operating_cost_band",
            "finance_need_band",
            "record_keeping",
            "sales_channels",
            "challenges",
            "support_interests",
            "goals",
            "additional_notes",
        ]
        widgets = {
            "registration_type": forms.RadioSelect,
            "production_summary": forms.Textarea(attrs={"rows": 3}),
            "goals": forms.Textarea(attrs={"rows": 3}),
            "additional_notes": forms.Textarea(attrs={"rows": 3}),
            "farm_size": forms.NumberInput(attrs={"min": "0", "step": "0.01"}),
        }
        help_texts = {
            "group_registration_number": (
                "Optional. Enter the organisation's registration number only, not a "
                "personal ID number or tax PIN."
            ),
            "farm_size": "Approximate area only. Do not enter coordinates or attach land documents.",
            "production_summary": (
                "Optional. Describe typical production and season. Avoid personal ID, "
                "bank account, or tax details."
            ),
            "sales_band": "Approximate annual farm/business sales; this is optional.",
            "operating_cost_band": "Approximate annual operating costs; this is optional.",
            "additional_notes": "Do not include ID numbers, PINs, account numbers, or passwords.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["registration_type"].choices = FarmerProfile.RegistrationType.choices
        self.fields["county"].choices = [("", "Select a county")] + [
            (county, county) for county in COUNTIES
        ]
        self.fields["group_type"].required = False
        self.fields["group_registration_status"].required = False
        self.fields["group_name"].label = "Group or association name *"
        self.fields["group_type"].label = "Organisation type *"
        self.fields["group_registration_status"].choices = [("", "Choose one (optional)")] + [
            choice
            for choice in FarmerProfile.RegistrationStatus.choices
            if choice[0] != FarmerProfile.RegistrationStatus.NOT_APPLICABLE
        ]
        self.fields["preferred_language"].label = "Preferred language"
        self.fields["farm_size_unit"].required = False
        if not self.is_bound:
            self.initial["group_registration_status"] = ""

    def clean(self):
        cleaned_data = super().clean()
        registration_type = cleaned_data.get("registration_type")
        if registration_type == FarmerProfile.RegistrationType.GROUP:
            for field in ("group_name", "group_type"):
                if not cleaned_data.get(field):
                    self.add_error(field, "This field is required for a group registration.")
            if not cleaned_data.get("group_authorization_confirmed"):
                self.add_error(
                    "group_authorization_confirmed",
                    "Confirm that you are authorised to register this group.",
                )
            if not cleaned_data.get("group_registration_status"):
                cleaned_data["group_registration_status"] = (
                    FarmerProfile.RegistrationStatus.PREFER_NOT
                )
        elif registration_type == FarmerProfile.RegistrationType.INDIVIDUAL:
            cleaned_data["group_name"] = ""
            cleaned_data["group_type"] = ""
            cleaned_data["group_registration_number"] = ""
            cleaned_data["group_member_count"] = None
            cleaned_data["representative_role"] = ""
            cleaned_data["group_authorization_confirmed"] = False
            cleaned_data["group_registration_status"] = (
                FarmerProfile.RegistrationStatus.NOT_APPLICABLE
            )

        self.instance.group_authorization_confirmed = bool(
            cleaned_data.get("group_authorization_confirmed")
        )
        self.instance.group_review_status = (
            FarmerProfile.EvidenceStatus.PENDING
            if registration_type == FarmerProfile.RegistrationType.GROUP
            else FarmerProfile.EvidenceStatus.NOT_APPLICABLE
        )

        preferred_contact = cleaned_data.get("preferred_contact")
        if preferred_contact == FarmerProfile.ContactPreference.EMAIL:
            if not cleaned_data.get("email"):
                self.add_error("email", "Enter an email address if you prefer email contact.")
        elif preferred_contact in {
            FarmerProfile.ContactPreference.PHONE,
            FarmerProfile.ContactPreference.WHATSAPP,
        } and not cleaned_data.get("phone"):
            self.add_error("phone", "Enter a phone number for your preferred contact method.")

        if cleaned_data.get("farm_size") and not cleaned_data.get("farm_size_unit"):
            self.add_error("farm_size_unit", "Choose acres or hectares.")

        if cleaned_data.get("website"):
            raise ValidationError("The registration could not be submitted. Please try again.")
        return cleaned_data

    def save(self, commit=True):
        profile = super().save(commit=False)
        profile.activities = self.cleaned_data["activities"]
        profile.water_sources = self.cleaned_data["water_sources"]
        profile.sales_channels = self.cleaned_data["sales_channels"]
        profile.challenges = self.cleaned_data["challenges"]
        profile.support_interests = self.cleaned_data["support_interests"]
        profile.group_authorization_confirmed = self.cleaned_data[
            "group_authorization_confirmed"
        ]
        if profile.registration_type == FarmerProfile.RegistrationType.GROUP:
            profile.group_review_status = FarmerProfile.EvidenceStatus.PENDING
        if commit:
            profile.save()
        return profile


class FarmerDocumentForm(forms.Form):
    document_type = forms.ChoiceField(
        choices=FarmerDocument.DocumentType.choices,
        label="Evidence type",
    )
    description = forms.CharField(
        required=False,
        max_length=200,
        label="Short description",
        help_text="Do not include ID numbers or other sensitive details in this description.",
    )
    file = forms.FileField(
        required=False,
        label="Choose a PDF, JPG, or PNG (maximum 5 MB)",
        widget=forms.ClearableFileInput(attrs={"accept": ".pdf,.jpg,.jpeg,.png"}),
    )

    def clean_file(self):
        uploaded = self.cleaned_data.get("file")
        if not uploaded:
            return None
        suffix = Path(uploaded.name).suffix.lower()
        if suffix not in {".pdf", ".jpg", ".jpeg", ".png"}:
            raise ValidationError("Upload a PDF, JPG, or PNG file.")
        if uploaded.size > MAX_DOCUMENT_SIZE:
            raise ValidationError("Each document must be no larger than 5 MB.")

        uploaded.seek(0)
        header = uploaded.read(8)
        uploaded.seek(0)
        if suffix == ".pdf":
            valid = header.startswith(b"%PDF-")
        elif suffix in {".jpg", ".jpeg"}:
            valid = header.startswith(b"\xff\xd8\xff")
        else:
            valid = header.startswith(b"\x89PNG\r\n\x1a\n")
        if not valid:
            raise ValidationError("The file contents do not match the selected file type.")

        if suffix in {".jpg", ".jpeg", ".png"}:
            try:
                with Image.open(uploaded) as image:
                    if image.width * image.height > Image.MAX_IMAGE_PIXELS:
                        raise ValidationError("The image dimensions are too large.")
                    image.verify()
            except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
                raise ValidationError("The image could not be safely read.") from exc
            finally:
                uploaded.seek(0)
        if settings.ANTIVIRUS_ENABLED:
            try:
                result = subprocess.run(
                    [settings.ANTIVIRUS_COMMAND, "--no-summary", "-"],
                    input=uploaded.read(),
                    capture_output=True,
                    timeout=30,
                    check=False,
                )
            except (OSError, subprocess.TimeoutExpired) as exc:
                logger.exception("The document malware scanner could not complete.")
                raise ValidationError(
                    "The evidence could not be scanned. Please try again later."
                ) from exc
            finally:
                uploaded.seek(0)
            if result.returncode != 0:
                logger.warning("A registration portal upload was rejected by the malware scanner.")
                raise ValidationError(
                    "The evidence could not be accepted. Check the file and try again."
                )
        return uploaded

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get("file") and cleaned_data.get("description", "").strip():
            self.add_error("file", "Choose a file or clear the description.")
        return cleaned_data


FarmerDocumentFormSet = formset_factory(
    FarmerDocumentForm,
    extra=0,
    max_num=MAX_DOCUMENTS_PER_REGISTRATION,
    validate_max=True,
    absolute_max=MAX_DOCUMENTS_PER_REGISTRATION,
)


class PartnerRegistrationForm(forms.ModelForm):
    roles = forms.MultipleChoiceField(
        choices=PARTNER_ROLE_CHOICES,
        required=True,
        widget=forms.CheckboxSelectMultiple,
        label="How would you like to work with MoFirms?",
    )
    operating_counties = forms.MultipleChoiceField(
        choices=[(county, county) for county in COUNTIES],
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Counties where you operate or deliver",
    )
    delivery_methods = forms.MultipleChoiceField(
        choices=PARTNER_DELIVERY_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="How do you deliver or collect?",
    )
    offer_categories = forms.MultipleChoiceField(
        choices=PARTNER_OFFER_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="What goods or services do you supply?",
    )
    produce_categories = forms.MultipleChoiceField(
        choices=PRODUCE_CATEGORY_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="What produce are you looking to buy?",
    )
    sourcing_counties = forms.MultipleChoiceField(
        choices=[(county, county) for county in COUNTIES],
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Where are you looking to source produce?",
    )
    engagement_interests = forms.MultipleChoiceField(
        choices=[
            ("supplier_referrals", "Be listed for farmer enquiries and referrals"),
            ("buyer_linkages", "Find farmer groups and produce suppliers"),
            ("project_work", "Explore projects or service contracts"),
            ("market_events", "Hear about matching and market events"),
        ],
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="What would you like from a MoFirms partnership?",
    )
    challenges = forms.MultipleChoiceField(
        choices=[
            ("customer_access", "Finding farmers, groups, or customers"),
            ("market_access", "Finding reliable buyers or suppliers"),
            ("logistics", "Transport, delivery, or storage"),
            ("quality", "Quality standards or consistency"),
            ("working_capital", "Working capital or payment timing"),
            ("business_visibility", "Business visibility and referrals"),
            ("contracting", "Contracts, procurement, or administration"),
            ("skills", "Skills or specialist capacity"),
            ("other", "Other"),
        ],
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="What challenges would a partnership help address?",
    )
    privacy_consent = forms.BooleanField(
        required=True,
        label=(
            "I agree that MoFirms may review this registration and contact me about "
            "my business, offerings, buying needs, and relevant partnership enquiries."
        ),
    )
    listing_consent = forms.BooleanField(
        required=False,
        label=(
            "Optional: I agree that MoFirms may share relevant details from my business "
            "profile directly with potential farmer or business partners to facilitate "
            "a referral. This is not permission to publish my contact details."
        ),
    )
    document_consent = forms.BooleanField(required=False)
    website_trap = forms.CharField(required=False, widget=forms.HiddenInput)

    class Meta:
        model = PartnerProfile
        fields = [
            "applicant_type",
            "roles",
            "contact_name",
            "business_name",
            "trading_name",
            "business_description",
            "phone",
            "email",
            "website",
            "preferred_contact",
            "preferred_language",
            "registration_status",
            "registration_number",
            "year_established",
            "years_experience",
            "business_size",
            "staff_band",
            "county",
            "sub_county",
            "ward",
            "operating_counties",
            "delivery_methods",
            "offer_categories",
            "offer_details",
            "service_description",
            "brands_or_products",
            "service_area",
            "lead_time",
            "minimum_order",
            "prices_and_terms",
            "produce_categories",
            "produce_details",
            "sourcing_counties",
            "buyer_capacity",
            "buying_frequency",
            "quality_requirements",
            "payment_terms",
            "clients_and_references",
            "licences_and_standards",
            "service_capacity",
            "staff_qualifications",
            "engagement_interests",
            "challenges",
            "partnership_goals",
            "additional_notes",
        ]
        widgets = {
            "applicant_type": forms.RadioSelect,
            "business_description": forms.Textarea(attrs={"rows": 3}),
            "offer_details": forms.Textarea(attrs={"rows": 3}),
            "service_description": forms.Textarea(attrs={"rows": 3}),
            "prices_and_terms": forms.Textarea(attrs={"rows": 3}),
            "produce_details": forms.Textarea(attrs={"rows": 3}),
            "quality_requirements": forms.Textarea(attrs={"rows": 3}),
            "clients_and_references": forms.Textarea(attrs={"rows": 3}),
            "licences_and_standards": forms.Textarea(attrs={"rows": 3}),
            "staff_qualifications": forms.Textarea(attrs={"rows": 3}),
            "partnership_goals": forms.Textarea(attrs={"rows": 3}),
            "additional_notes": forms.Textarea(attrs={"rows": 3}),
            "registration_number": forms.TextInput(attrs={"autocomplete": "off"}),
            "year_established": forms.NumberInput(
                attrs={"min": "1800", "max": "2100", "inputmode": "numeric"}
            ),
        }
        help_texts = {
            "registration_number": (
                "Business registration number only. Do not enter a personal ID number, "
                "KRA PIN, bank account, or password."
            ),
            "website": "Optional public business website. Do not enter a sign-in or private link.",
            "business_size": "Approximate scale; do not enter revenue or account details.",
            "staff_band": "Approximate team capacity, not a staff list.",
            "prices_and_terms": "Indicative only; do not enter confidential contract or bank details.",
            "clients_and_references": (
                "Share reference names or organisations only if you have permission to do so."
            ),
            "licences_and_standards": (
                "List relevant licence names and their issuing bodies. Do not include passwords "
                "or tax PINs."
            ),
            "additional_notes": (
                "Do not enter personal ID numbers, tax PINs, bank details, passwords, "
                "or confidential customer data."
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["county"].choices = [("", "Select a county")] + [
            (county, county) for county in COUNTIES
        ]
        self.fields["applicant_type"].choices = PartnerProfile.ApplicantType.choices
        self.fields["applicant_type"].label = "Who does this profile represent?"
        self.fields["business_name"].label = "Legal or registered business name"
        self.fields["registration_status"].required = False
        self.fields["registration_status"].choices = [("", "Choose one (optional)")] + [
            choice for choice in PartnerProfile.RegistrationStatus.choices
        ]
        self.fields["business_size"].required = False
        self.fields["staff_band"].required = False
        self.fields["buyer_capacity"].required = False
        self.fields["service_capacity"].required = False

    def clean(self):
        cleaned_data = super().clean()
        applicant_type = cleaned_data.get("applicant_type")
        roles = cleaned_data.get("roles", [])

        if applicant_type == PartnerProfile.ApplicantType.BUSINESS and not cleaned_data.get(
            "business_name", ""
        ).strip():
            self.add_error("business_name", "Enter the name the organisation trades or registers under.")
        if not cleaned_data.get("registration_status"):
            cleaned_data["registration_status"] = PartnerProfile.RegistrationStatus.NOT_REGISTERED

        preferred_contact = cleaned_data.get("preferred_contact")
        if (
            preferred_contact == PartnerProfile.ContactPreference.EMAIL
            and not cleaned_data.get("email")
        ):
            self.add_error("email", "Enter an email address for your preferred contact method.")
        elif (
            preferred_contact in {
                PartnerProfile.ContactPreference.PHONE,
                PartnerProfile.ContactPreference.WHATSAPP,
            }
            and not cleaned_data.get("phone")
        ):
            self.add_error("phone", "Enter a phone number for your preferred contact method.")

        if "supplier" in roles:
            if not cleaned_data.get("offer_categories"):
                self.add_error("offer_categories", "Select at least one product or service you provide.")
            if not cleaned_data.get("offer_details", "").strip():
                self.add_error("offer_details", "Briefly describe what you supply and your availability.")
        if "buyer" in roles:
            if not cleaned_data.get("produce_categories"):
                self.add_error("produce_categories", "Select at least one type of produce you buy.")
            if not cleaned_data.get("produce_details", "").strip():
                self.add_error("produce_details", "Describe the produce you buy and any key specifications.")
        if (
            "service_provider" in roles
            and not cleaned_data.get("service_description", "").strip()
        ):
            self.add_error(
                "service_description",
                "Describe your services and the people or areas you serve.",
            )

        if cleaned_data.get("website_trap"):
            raise ValidationError("The registration could not be submitted. Please try again.")
        return cleaned_data

    def save(self, commit=True):
        profile = super().save(commit=False)
        for field in (
            "roles",
            "operating_counties",
            "delivery_methods",
            "offer_categories",
            "produce_categories",
            "sourcing_counties",
            "engagement_interests",
            "challenges",
        ):
            setattr(profile, field, self.cleaned_data[field])
        if (
            profile.applicant_type == PartnerProfile.ApplicantType.INDIVIDUAL
            and not profile.business_name
        ):
            profile.registration_status = PartnerProfile.RegistrationStatus.NOT_REGISTERED
        if commit:
            profile.save()
        return profile


class PartnerDocumentForm(FarmerDocumentForm):
    document_type = forms.ChoiceField(
        choices=PartnerDocument.DocumentType.choices,
        label="Evidence type",
    )


PartnerDocumentFormSet = formset_factory(
    PartnerDocumentForm,
    extra=0,
    max_num=MAX_DOCUMENTS_PER_REGISTRATION,
    validate_max=True,
    absolute_max=MAX_DOCUMENTS_PER_REGISTRATION,
)


class FinancialAnalysisRequestForm(forms.ModelForm):
    services_requested = forms.MultipleChoiceField(
        choices=[
            ("statement_review", "Financial statement or accounts review"),
            ("business_plan", "Business plan development or review"),
            ("cash_flow", "Cash-flow analysis"),
            ("budget_forecast", "Budget or financial forecast"),
            ("funding_readiness", "Funding or lender readiness"),
            ("other", "Other financial analysis"),
        ],
        required=True,
        widget=forms.CheckboxSelectMultiple,
        label="What financial support do you need?",
    )
    records_available = forms.MultipleChoiceField(
        choices=[
            ("financial_statements", "Financial statements"),
            ("sales_records", "Sales or income records"),
            ("expense_records", "Expense or purchase records"),
            ("cashbook", "Cashbook or bookkeeping records"),
            ("bank_statements", "Bank statements"),
            ("business_plan", "Existing business plan"),
            ("budgets", "Budgets or forecasts"),
            ("none", "I do not have formal records yet"),
        ],
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Which records are available?",
    )
    privacy_consent = forms.BooleanField(
        required=True,
        label=(
            "I agree that MoFirms may review this request and contact me about its scope "
            "and a possible fee quote."
        ),
    )
    website_trap = forms.CharField(required=False, widget=forms.HiddenInput)

    class Meta:
        model = FinancialAnalysisRequest
        fields = [
            "applicant_type",
            "contact_name",
            "business_name",
            "phone",
            "email",
            "preferred_contact",
            "county",
            "sector",
            "services_requested",
            "financial_period",
            "records_available",
            "accounting_software",
            "annual_revenue_band",
            "funding_need_band",
            "timeline",
            "request_summary",
        ]
        widgets = {
            "applicant_type": forms.RadioSelect,
            "request_summary": forms.Textarea(attrs={"rows": 4}),
        }
        help_texts = {
            "financial_period": "For example, January–December 2025. Approximate dates are fine.",
            "accounting_software": "Optional. Do not enter account names, passwords, or sign-in links.",
            "annual_revenue_band": "Optional estimate only; do not enter exact account balances.",
            "funding_need_band": "Optional estimate only; submitting a request is not a loan application.",
            "request_summary": (
                "Describe the decision or output you need. Do not include passwords, account "
                "numbers, personal ID numbers, tax PINs, or unrelated people's data."
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["county"].choices = [("", "Select a county")] + [
            (county, county) for county in COUNTIES
        ]
        self.fields["business_name"].required = False
        self.fields["phone"].required = False
        self.fields["email"].required = False
        self.fields["sector"].required = False
        self.fields["financial_period"].required = False
        self.fields["accounting_software"].required = False
        self.fields["annual_revenue_band"].required = False
        self.fields["funding_need_band"].required = False
        self.fields["timeline"].required = False

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("website_trap"):
            raise ValidationError("The request could not be submitted. Please try again.")
        return cleaned_data

    def save(self, commit=True):
        request = super().save(commit=False)
        request.services_requested = self.cleaned_data["services_requested"]
        request.records_available = self.cleaned_data["records_available"]
        if commit:
            request.save()
        return request


class FinancialAnalysisDocumentForm(FarmerDocumentForm):
    document_type = forms.ChoiceField(
        choices=FinancialAnalysisDocument.DocumentType.choices,
        label="Document type",
    )


FinancialAnalysisDocumentFormSet = formset_factory(
    FinancialAnalysisDocumentForm,
    extra=0,
    max_num=MAX_DOCUMENTS_PER_REGISTRATION,
    validate_max=True,
    absolute_max=MAX_DOCUMENTS_PER_REGISTRATION,
)


def sanitize_uploaded_image(uploaded):
    suffix = Path(uploaded.name).suffix.lower()
    if suffix == ".pdf":
        uploaded.seek(0)
        return uploaded

    uploaded.seek(0)
    with Image.open(uploaded) as source:
        image = ImageOps.exif_transpose(source)
        output = BytesIO()
        if suffix in {".jpg", ".jpeg"}:
            if image.mode not in {"RGB", "L"}:
                image = image.convert("RGB")
            image.save(output, format="JPEG", optimize=True)
            extension = ".jpg"
        else:
            if image.mode not in {"RGB", "RGBA", "L"}:
                image = image.convert("RGBA")
            image.save(output, format="PNG", optimize=True)
            extension = ".png"
    safe_bytes = output.getvalue()
    if len(safe_bytes) > MAX_DOCUMENT_SIZE:
        raise ValidationError(
            "The image is larger than 5 MB after removing its embedded metadata."
        )
    return ContentFile(safe_bytes, name=f"{uuid.uuid4().hex}{extension}")
