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
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from PIL import Image, ImageOps, UnidentifiedImageError

from .templatetags.custom_i18n import localize_choices, translate
from .models import (
    ACTIVITY_CHOICES,
    COUNTIES,
    ConsultationLead,
    PARTNER_DELIVERY_CHOICES,
    PARTNER_OFFER_CHOICES,
    PARTNER_ROLE_CHOICES,
    PRODUCE_CATEGORY_CHOICES,
    SUPPORT_CHOICES,
    FarmerDocument,
    FarmerProfile,
    FinancialAnalysisDocument,
    FinancialAnalysisRequest,
    NewsletterSubscription,
    PartnerDocument,
    PartnerProfile,
    RiskAssessmentDocument,
    RiskAssessmentRequest,
    ResearchQuestion,
    ResearchStudy,
    ResearcherApplication,
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
    research_invite_consent = forms.BooleanField(
        required=False,
        label=(
            "Optional: I consent to MoFirms contacting me about research surveys. "
            "This does not enroll me or disclose my contact details to researchers. "
            "For a group, each respondent must separately choose to participate."
        ),
    )
    website = forms.CharField(required=False, widget=forms.HiddenInput)
    group_authorization_confirmed = forms.BooleanField(
        required=False,
        label="I am authorised to submit information for this group and have informed its members.",
    )
    create_account = forms.BooleanField(
        required=False,
        label="Create an account so I can sign in later and check my registration status.",
    )
    password1 = forms.CharField(
        label="Password",
        required=False,
        strip=False,
        widget=forms.PasswordInput,
        help_text="Only needed if you tick \"Create an account\" above.",
    )
    password2 = forms.CharField(
        label="Confirm password",
        required=False,
        strip=False,
        widget=forms.PasswordInput,
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

    def __init__(self, *args, lang="en", **kwargs):
        super().__init__(*args, **kwargs)
        self.lang = lang
        self.fields["activities"].label = translate("field.farmer.activities", lang)
        self.fields["activities"].choices = localize_choices(ACTIVITY_CHOICES, lang, "choice.activity")
        self.fields["water_sources"].label = translate("field.farmer.water_sources", lang)
        self.fields["water_sources"].choices = localize_choices(
            FarmerProfile.WaterSource.choices, lang, "choice.water_source"
        )
        self.fields["sales_channels"].label = translate("field.farmer.sales_channels", lang)
        self.fields["sales_channels"].choices = localize_choices(
            self.fields["sales_channels"].choices, lang, "choice.sales_channel"
        )
        self.fields["challenges"].label = translate("field.farmer.challenges", lang)
        self.fields["challenges"].choices = localize_choices(
            self.fields["challenges"].choices, lang, "choice.farmer_challenge"
        )
        self.fields["support_interests"].label = translate("field.farmer.support_interests", lang)
        self.fields["support_interests"].choices = localize_choices(
            SUPPORT_CHOICES, lang, "choice.support"
        )
        self.fields["privacy_consent"].label = translate("field.farmer.privacy_consent", lang)
        self.fields["research_invite_consent"].label = translate(
            "field.farmer.research_invite_consent", lang
        )
        self.fields["group_authorization_confirmed"].label = translate(
            "field.farmer.group_authorization_confirmed", lang
        )
        self.fields["create_account"].label = translate("field.farmer.create_account", lang)
        self.fields["password1"].label = translate("field.farmer.password1", lang)
        self.fields["password1"].help_text = translate("help.farmer.password1", lang)
        self.fields["password2"].label = translate("field.farmer.password2", lang)
        self.fields["group_registration_number"].help_text = translate(
            "help.farmer.group_registration_number", lang
        )
        self.fields["farm_size"].help_text = translate("help.farmer.farm_size", lang)
        self.fields["production_summary"].help_text = translate(
            "help.farmer.production_summary", lang
        )
        self.fields["sales_band"].help_text = translate("help.farmer.sales_band", lang)
        self.fields["operating_cost_band"].help_text = translate(
            "help.farmer.operating_cost_band", lang
        )
        self.fields["additional_notes"].help_text = translate(
            "help.farmer.additional_notes", lang
        )
        self.fields["registration_type"].choices = localize_choices(
            FarmerProfile.RegistrationType.choices, lang, "choice.registration_type"
        )
        self.fields["county"].choices = [("", translate("choice.select_county", lang))] + [
            (county, county) for county in COUNTIES
        ]
        self.fields["group_type"].required = False
        self.fields["group_registration_status"].required = False
        self.fields["group_name"].label = translate("field.farmer.group_name", lang)
        self.fields["group_type"].label = translate("field.farmer.group_type", lang)
        self.fields["group_type"].choices = localize_choices(
            FarmerProfile.GroupType.choices, lang, "choice.group_type"
        )
        self.fields["group_registration_status"].choices = [
            ("", translate("choice.registration_status.choose_optional", lang))
        ] + localize_choices(
            [
                choice
                for choice in FarmerProfile.RegistrationStatus.choices
                if choice[0] != FarmerProfile.RegistrationStatus.NOT_APPLICABLE
            ],
            lang,
            "choice.registration_status",
        )
        self.fields["preferred_contact"].choices = localize_choices(
            FarmerProfile.ContactPreference.choices, lang, "choice.contact_preference"
        )
        self.fields["preferred_language"].label = translate(
            "field.farmer.preferred_language", lang
        )
        self.fields["farm_size_unit"].required = False
        self.fields["farm_size_unit"].choices = localize_choices(
            FarmerProfile.AreaUnit.choices, lang, "choice.area_unit"
        )
        self.fields["land_access"].choices = localize_choices(
            FarmerProfile.LandAccess.choices, lang, "choice.land_access"
        )
        self.fields["years_farming"].choices = localize_choices(
            FarmerProfile.Experience.choices, lang, "choice.experience"
        )
        for field_name in ("sales_band", "operating_cost_band", "finance_need_band"):
            self.fields[field_name].choices = localize_choices(
                FarmerProfile.FinancialBand.choices, lang, "choice.financial_band"
            )
        self.fields["record_keeping"].choices = localize_choices(
            FarmerProfile.RecordKeeping.choices, lang, "choice.record_keeping"
        )
        if not self.is_bound:
            self.initial["group_registration_status"] = ""

    def clean(self):
        cleaned_data = super().clean()
        registration_type = cleaned_data.get("registration_type")
        if registration_type == FarmerProfile.RegistrationType.GROUP:
            for field in ("group_name", "group_type"):
                if not cleaned_data.get(field):
                    self.add_error(field, translate("err.farmer.group_field_required", self.lang))
            if not cleaned_data.get("group_authorization_confirmed"):
                self.add_error(
                    "group_authorization_confirmed",
                    translate("err.farmer.group_authorization_required", self.lang),
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
                self.add_error("email", translate("err.farmer.email_required_for_contact", self.lang))
        elif preferred_contact in {
            FarmerProfile.ContactPreference.PHONE,
            FarmerProfile.ContactPreference.WHATSAPP,
        } and not cleaned_data.get("phone"):
            self.add_error("phone", translate("err.farmer.phone_required_for_contact", self.lang))

        if cleaned_data.get("farm_size") and not cleaned_data.get("farm_size_unit"):
            self.add_error("farm_size_unit", translate("err.farmer.farm_size_unit_required", self.lang))

        if cleaned_data.get("create_account"):
            email = cleaned_data.get("email", "").strip().lower()
            password1 = cleaned_data.get("password1")
            password2 = cleaned_data.get("password2")
            if not email:
                self.add_error("email", translate("err.farmer.account_email_required", self.lang))
            elif get_user_model().objects.filter(email__iexact=email).exists():
                self.add_error("email", translate("err.farmer.account_email_taken", self.lang))
            if not password1:
                self.add_error("password1", translate("err.farmer.password_required", self.lang))
            if not password2:
                self.add_error("password2", translate("err.farmer.password_confirm_required", self.lang))
            if password1 and password2 and password1 != password2:
                self.add_error("password2", translate("err.farmer.passwords_mismatch", self.lang))
            if password1 and email:
                candidate = get_user_model()(username=email, email=email)
                try:
                    validate_password(password1, candidate)
                except ValidationError as error:
                    self.add_error("password1", error)

        if cleaned_data.get("website"):
            raise ValidationError(translate("err.farmer.submission_failed", self.lang))
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
    document_type_choice_prefix = "choice.farmer_document_type"
    document_type_label_key = "field.document.type"

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

    def __init__(self, *args, lang="en", **kwargs):
        super().__init__(*args, **kwargs)
        self.lang = lang
        self.fields["document_type"].label = translate(self.document_type_label_key, lang)
        self.fields["document_type"].choices = localize_choices(
            self.fields["document_type"].choices, lang, self.document_type_choice_prefix
        )
        self.fields["description"].label = translate("field.document.description", lang)
        self.fields["description"].help_text = translate("help.document.description", lang)
        self.fields["file"].label = translate("field.document.file", lang)

    def clean_file(self):
        uploaded = self.cleaned_data.get("file")
        if not uploaded:
            return None
        suffix = Path(uploaded.name).suffix.lower()
        if suffix not in {".pdf", ".jpg", ".jpeg", ".png"}:
            raise ValidationError(translate("err.document.invalid_type", self.lang))
        if uploaded.size > MAX_DOCUMENT_SIZE:
            raise ValidationError(translate("err.document.too_large", self.lang))

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
            raise ValidationError(translate("err.document.content_mismatch", self.lang))

        if suffix in {".jpg", ".jpeg", ".png"}:
            try:
                with Image.open(uploaded) as image:
                    if image.width * image.height > Image.MAX_IMAGE_PIXELS:
                        raise ValidationError(translate("err.document.dimensions_too_large", self.lang))
                    image.verify()
            except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
                raise ValidationError(translate("err.document.unreadable_image", self.lang)) from exc
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
                    translate("err.document.scan_failed", self.lang)
                ) from exc
            finally:
                uploaded.seek(0)
            if result.returncode != 0:
                logger.warning("A registration portal upload was rejected by the malware scanner.")
                raise ValidationError(
                    translate("err.document.rejected_by_scanner", self.lang)
                )
        return uploaded

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get("file") and cleaned_data.get("description", "").strip():
            self.add_error("file", translate("err.document.choose_file_or_clear", self.lang))
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
    research_invite_consent = forms.BooleanField(
        required=False,
        label=(
            "Optional: I consent to MoFirms contacting me about research surveys. "
            "This does not enroll me or disclose my contact details to researchers."
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

    def __init__(self, *args, lang="en", **kwargs):
        super().__init__(*args, **kwargs)
        self.lang = lang
        self.fields["roles"].label = translate("field.partner.roles", lang)
        self.fields["roles"].choices = localize_choices(PARTNER_ROLE_CHOICES, lang, "choice.partner_role")
        self.fields["operating_counties"].label = translate("field.partner.operating_counties", lang)
        self.fields["delivery_methods"].label = translate("field.partner.delivery_methods", lang)
        self.fields["delivery_methods"].choices = localize_choices(
            PARTNER_DELIVERY_CHOICES, lang, "choice.partner_delivery"
        )
        self.fields["offer_categories"].label = translate("field.partner.offer_categories", lang)
        self.fields["offer_categories"].choices = localize_choices(
            PARTNER_OFFER_CHOICES, lang, "choice.partner_offer"
        )
        self.fields["produce_categories"].label = translate("field.partner.produce_categories", lang)
        self.fields["produce_categories"].choices = localize_choices(
            PRODUCE_CATEGORY_CHOICES, lang, "choice.produce_category"
        )
        self.fields["sourcing_counties"].label = translate("field.partner.sourcing_counties", lang)
        self.fields["engagement_interests"].label = translate(
            "field.partner.engagement_interests", lang
        )
        self.fields["engagement_interests"].choices = localize_choices(
            self.fields["engagement_interests"].choices, lang, "choice.partner_engagement"
        )
        self.fields["challenges"].label = translate("field.partner.challenges", lang)
        self.fields["challenges"].choices = localize_choices(
            self.fields["challenges"].choices, lang, "choice.partner_challenge"
        )
        self.fields["privacy_consent"].label = translate("field.partner.privacy_consent", lang)
        self.fields["listing_consent"].label = translate("field.partner.listing_consent", lang)
        self.fields["research_invite_consent"].label = translate(
            "field.partner.research_invite_consent", lang
        )
        self.fields["registration_number"].help_text = translate(
            "help.partner.registration_number", lang
        )
        self.fields["website"].help_text = translate("help.partner.website", lang)
        self.fields["business_size"].help_text = translate("help.partner.business_size", lang)
        self.fields["staff_band"].help_text = translate("help.partner.staff_band", lang)
        self.fields["prices_and_terms"].help_text = translate(
            "help.partner.prices_and_terms", lang
        )
        self.fields["clients_and_references"].help_text = translate(
            "help.partner.clients_and_references", lang
        )
        self.fields["licences_and_standards"].help_text = translate(
            "help.partner.licences_and_standards", lang
        )
        self.fields["additional_notes"].help_text = translate(
            "help.partner.additional_notes", lang
        )
        self.fields["county"].choices = [("", translate("choice.select_county", lang))] + [
            (county, county) for county in COUNTIES
        ]
        self.fields["applicant_type"].choices = localize_choices(
            PartnerProfile.ApplicantType.choices, lang, "choice.applicant_type.partner"
        )
        self.fields["applicant_type"].label = translate("field.partner.applicant_type", lang)
        self.fields["business_name"].label = translate("field.partner.business_name", lang)
        self.fields["registration_status"].required = False
        self.fields["registration_status"].choices = [
            ("", translate("choice.registration_status.choose_optional", lang))
        ] + localize_choices(
            PartnerProfile.RegistrationStatus.choices, lang, "choice.registration_status"
        )
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
            self.add_error("business_name", translate("err.partner.business_name_required", self.lang))
        if not cleaned_data.get("registration_status"):
            cleaned_data["registration_status"] = PartnerProfile.RegistrationStatus.NOT_REGISTERED

        preferred_contact = cleaned_data.get("preferred_contact")
        if (
            preferred_contact == PartnerProfile.ContactPreference.EMAIL
            and not cleaned_data.get("email")
        ):
            self.add_error("email", translate("err.partner.email_required_for_contact", self.lang))
        elif (
            preferred_contact in {
                PartnerProfile.ContactPreference.PHONE,
                PartnerProfile.ContactPreference.WHATSAPP,
            }
            and not cleaned_data.get("phone")
        ):
            self.add_error("phone", translate("err.partner.phone_required_for_contact", self.lang))

        if "supplier" in roles:
            if not cleaned_data.get("offer_categories"):
                self.add_error("offer_categories", translate("err.partner.offer_categories_required", self.lang))
            if not cleaned_data.get("offer_details", "").strip():
                self.add_error("offer_details", translate("err.partner.offer_details_required", self.lang))
        if "buyer" in roles:
            if not cleaned_data.get("produce_categories"):
                self.add_error("produce_categories", translate("err.partner.produce_categories_required", self.lang))
            if not cleaned_data.get("produce_details", "").strip():
                self.add_error("produce_details", translate("err.partner.produce_details_required", self.lang))
        if (
            "service_provider" in roles
            and not cleaned_data.get("service_description", "").strip()
        ):
            self.add_error(
                "service_description",
                translate("err.partner.service_description_required", self.lang),
            )

        if cleaned_data.get("website_trap"):
            raise ValidationError(translate("err.partner.submission_failed", self.lang))
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
    document_type_choice_prefix = "choice.partner_document_type"

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

    def __init__(self, *args, lang="en", **kwargs):
        super().__init__(*args, **kwargs)
        self.lang = lang
        self.fields["services_requested"].label = translate(
            "field.financial.services_requested", lang
        )
        self.fields["services_requested"].choices = localize_choices(
            self.fields["services_requested"].choices, lang, "choice.financial_service"
        )
        self.fields["records_available"].label = translate(
            "field.financial.records_available", lang
        )
        self.fields["records_available"].choices = localize_choices(
            self.fields["records_available"].choices, lang, "choice.records_available"
        )
        self.fields["privacy_consent"].label = translate("field.financial.privacy_consent", lang)
        self.fields["financial_period"].help_text = translate(
            "help.financial.financial_period", lang
        )
        self.fields["accounting_software"].help_text = translate(
            "help.financial.accounting_software", lang
        )
        self.fields["annual_revenue_band"].help_text = translate(
            "help.financial.annual_revenue_band", lang
        )
        self.fields["funding_need_band"].help_text = translate(
            "help.financial.funding_need_band", lang
        )
        self.fields["request_summary"].help_text = translate(
            "help.financial.request_summary", lang
        )
        self.fields["applicant_type"].choices = localize_choices(
            FinancialAnalysisRequest.ApplicantType.choices, lang, "choice.applicant_type.general"
        )
        self.fields["county"].choices = [("", translate("choice.select_county", lang))] + [
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
            raise ValidationError(translate("err.financial.submission_failed", self.lang))
        return cleaned_data

    def save(self, commit=True):
        request = super().save(commit=False)
        request.services_requested = self.cleaned_data["services_requested"]
        request.records_available = self.cleaned_data["records_available"]
        if commit:
            request.save()
        return request


class BusinessReadinessForm(forms.ModelForm):
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
            "and any proposed fee."
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
            "business_goal",
            "current_challenge",
            "average_monthly_sales",
            "average_monthly_costs",
            "financial_period",
            "records_available",
            "annual_revenue_band",
            "seasonality_notes",
        ]
        widgets = {
            "applicant_type": forms.RadioSelect,
            "business_goal": forms.Textarea(attrs={"rows": 3}),
            "current_challenge": forms.Textarea(attrs={"rows": 3}),
            "financial_period": forms.TextInput(
                attrs={"placeholder": "For example, Jan-Dec 2025"}
            ),
            "seasonality_notes": forms.Textarea(attrs={"rows": 2}),
        }
        labels = {
            "average_monthly_sales": "Approximate average monthly sales (KSh)",
            "average_monthly_costs": "Approximate average monthly operating costs (KSh)",
        }
        help_texts = {
            "average_monthly_sales": "Optional estimate. Do not enter bank balances or account numbers.",
            "average_monthly_costs": "Optional estimate for the same period as monthly sales.",
            "financial_period": "Optional period covered by the records or estimates.",
            "business_goal": "What would you like the farm or enterprise to achieve?",
            "current_challenge": "What is the main issue you would like help addressing?",
            "seasonality_notes": "Optional: note months when sales, production, or costs change.",
        }

    def __init__(self, *args, lang="en", **kwargs):
        super().__init__(*args, **kwargs)
        self.lang = lang
        self.instance.request_type = (
            FinancialAnalysisRequest.RequestType.BUSINESS_READINESS
        )
        self.instance.services_requested = [
            "business_plan",
            "cash_flow",
            "funding_readiness",
        ]
        self.fields["records_available"].label = translate(
            "field.business_readiness.records_available", lang
        )
        self.fields["records_available"].choices = localize_choices(
            self.fields["records_available"].choices, lang, "choice.records_available"
        )
        self.fields["privacy_consent"].label = translate(
            "field.business_readiness.privacy_consent", lang
        )
        self.fields["average_monthly_sales"].label = translate(
            "field.business_readiness.average_monthly_sales", lang
        )
        self.fields["average_monthly_sales"].help_text = translate(
            "help.business_readiness.average_monthly_sales", lang
        )
        self.fields["average_monthly_costs"].label = translate(
            "field.business_readiness.average_monthly_costs", lang
        )
        self.fields["average_monthly_costs"].help_text = translate(
            "help.business_readiness.average_monthly_costs", lang
        )
        self.fields["financial_period"].help_text = translate(
            "help.business_readiness.financial_period", lang
        )
        self.fields["business_goal"].help_text = translate(
            "help.business_readiness.business_goal", lang
        )
        self.fields["current_challenge"].help_text = translate(
            "help.business_readiness.current_challenge", lang
        )
        self.fields["seasonality_notes"].help_text = translate(
            "help.business_readiness.seasonality_notes", lang
        )
        self.fields["applicant_type"].choices = localize_choices(
            FinancialAnalysisRequest.ApplicantType.choices, lang, "choice.applicant_type.general"
        )
        self.fields["county"].choices = [("", translate("choice.select_county", lang))] + [
            (county, county) for county in COUNTIES
        ]
        for field_name in ("business_name", "phone", "email", "sector"):
            self.fields[field_name].required = False

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("website_trap"):
            raise ValidationError(translate("err.business_readiness.submission_failed", self.lang))
        if (
            "none" in cleaned_data.get("records_available", [])
            and len(cleaned_data["records_available"]) > 1
        ):
            self.add_error(
                "records_available",
                translate("err.business_readiness.records_none_alone", self.lang),
            )
        sales = cleaned_data.get("average_monthly_sales")
        costs = cleaned_data.get("average_monthly_costs")
        if (sales is None) != (costs is None):
            raise ValidationError(
                translate("err.business_readiness.sales_costs_both_or_neither", self.lang)
            )
        return cleaned_data

    def save(self, commit=True):
        readiness_request = super().save(commit=False)
        readiness_request.request_type = (
            FinancialAnalysisRequest.RequestType.BUSINESS_READINESS
        )
        readiness_request.services_requested = [
            "business_plan",
            "cash_flow",
            "funding_readiness",
        ]
        readiness_request.records_available = self.cleaned_data["records_available"]
        readiness_request.request_summary = (
            f"Business goal: {self.cleaned_data['business_goal'].strip()}\n"
            f"Main challenge: {self.cleaned_data['current_challenge'].strip()}"
        )
        if commit:
            readiness_request.save()
        return readiness_request


class FinancialAnalysisDocumentForm(FarmerDocumentForm):
    document_type_choice_prefix = "choice.financial_document_type"
    document_type_label_key = "field.document.type_financial"

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


class RiskAssessmentRequestForm(forms.ModelForm):
    assessment_areas = forms.MultipleChoiceField(
        choices=[
            ("enterprise", "Business model and enterprise resilience"),
            ("market", "Markets, customers, and competition"),
            ("operations", "Production and day-to-day operations"),
            ("financial_resilience", "Financial resilience and exposure"),
            ("climate_environment", "Climate and environmental factors"),
            ("supply_chain", "Suppliers, logistics, and value chain"),
            ("governance_compliance", "Governance and compliance"),
            ("technology", "Technology and data"),
            ("other", "Other or not sure"),
        ],
        widget=forms.CheckboxSelectMultiple,
        label="What should the assessment cover?",
    )
    risk_priorities = forms.MultipleChoiceField(
        choices=[
            ("production", "Production, pests, disease, or input access"),
            ("climate", "Weather, water, or climate exposure"),
            ("market", "Price changes, buyer access, or competition"),
            ("financial", "Cash flow, cost changes, or funding exposure"),
            ("operations", "People, equipment, process, or continuity"),
            ("supply_chain", "Suppliers, transport, storage, or delivery"),
            ("governance", "Management, records, or decision-making"),
            ("regulatory", "Licensing, standards, or regulatory changes"),
            ("technology", "Technology access, reliability, or data"),
            ("not_sure", "I am not sure yet; help us scope the risks"),
        ],
        widget=forms.CheckboxSelectMultiple,
        label="Which risks or uncertainties matter most?",
    )
    opportunity_priorities = forms.MultipleChoiceField(
        choices=[
            ("market_growth", "New markets, customers, or buyer relationships"),
            ("value_addition", "Processing, storage, or value addition"),
            ("productivity", "Productivity, quality, or cost improvements"),
            ("climate_resilience", "Climate adaptation or resource efficiency"),
            ("digital", "Digital tools or better business information"),
            ("partnerships", "Partnerships, aggregation, or collaboration"),
            ("finance_readiness", "Investment or finance readiness"),
            ("new_products", "New products or services"),
            ("not_sure", "I am not sure yet; help identify opportunities"),
        ],
        widget=forms.CheckboxSelectMultiple,
        label="What opportunities would you like to explore?",
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
        model = RiskAssessmentRequest
        fields = [
            "applicant_type",
            "contact_name",
            "business_name",
            "phone",
            "email",
            "preferred_contact",
            "county",
            "sector",
            "enterprise_stage",
            "assessment_areas",
            "risk_priorities",
            "opportunity_priorities",
            "time_horizon",
            "request_summary",
        ]
        widgets = {
            "applicant_type": forms.RadioSelect,
            "request_summary": forms.Textarea(attrs={"rows": 5}),
        }
        help_texts = {
            "business_name": "Required for a business, group, or organisation.",
            "sector": "For example, dairy, horticulture, produce trading, or farm services.",
            "request_summary": (
                "Describe the decision you are considering, the main concern or opportunity, "
                "and what a useful assessment should help you understand. Do not include "
                "passwords, ID numbers, tax PINs, account numbers, or confidential third-party data."
            ),
        }

    def __init__(self, *args, lang="en", **kwargs):
        super().__init__(*args, **kwargs)
        self.lang = lang
        self.fields["assessment_areas"].label = translate("field.risk.assessment_areas", lang)
        self.fields["assessment_areas"].choices = localize_choices(
            self.fields["assessment_areas"].choices, lang, "choice.assessment_area"
        )
        self.fields["risk_priorities"].label = translate("field.risk.risk_priorities", lang)
        self.fields["risk_priorities"].choices = localize_choices(
            self.fields["risk_priorities"].choices, lang, "choice.risk_priority"
        )
        self.fields["opportunity_priorities"].label = translate(
            "field.risk.opportunity_priorities", lang
        )
        self.fields["opportunity_priorities"].choices = localize_choices(
            self.fields["opportunity_priorities"].choices, lang, "choice.opportunity_priority"
        )
        self.fields["privacy_consent"].label = translate("field.risk.privacy_consent", lang)
        self.fields["business_name"].help_text = translate("help.risk.business_name", lang)
        self.fields["sector"].help_text = translate("help.risk.sector", lang)
        self.fields["request_summary"].help_text = translate("help.risk.request_summary", lang)
        self.fields["applicant_type"].choices = localize_choices(
            RiskAssessmentRequest.ApplicantType.choices, lang, "choice.applicant_type.general"
        )
        self.fields["enterprise_stage"].choices = localize_choices(
            RiskAssessmentRequest.EnterpriseStage.choices, lang, "choice.enterprise_stage"
        )
        self.fields["time_horizon"].choices = localize_choices(
            RiskAssessmentRequest.TimeHorizon.choices, lang, "choice.time_horizon"
        )
        self.fields["county"].choices = [("", translate("choice.select_county", lang))] + [
            (county, county) for county in COUNTIES
        ]
        self.fields["business_name"].required = False
        self.fields["phone"].required = False
        self.fields["email"].required = False
        self.fields["sector"].required = False
        self.fields["enterprise_stage"].required = False

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("website_trap"):
            raise ValidationError(translate("err.risk.submission_failed", self.lang))
        return cleaned_data

    def save(self, commit=True):
        assessment_request = super().save(commit=False)
        assessment_request.assessment_areas = self.cleaned_data["assessment_areas"]
        assessment_request.risk_priorities = self.cleaned_data["risk_priorities"]
        assessment_request.opportunity_priorities = self.cleaned_data["opportunity_priorities"]
        if commit:
            assessment_request.save()
        return assessment_request


class RiskAssessmentDocumentForm(FarmerDocumentForm):
    document_type_choice_prefix = "choice.risk_document_type"
    document_type_label_key = "field.document.type_financial"

    document_type = forms.ChoiceField(
        choices=RiskAssessmentDocument.DocumentType.choices,
        label="Document type",
    )


RiskAssessmentDocumentFormSet = formset_factory(
    RiskAssessmentDocumentForm,
    extra=0,
    max_num=MAX_DOCUMENTS_PER_REGISTRATION,
    validate_max=True,
    absolute_max=MAX_DOCUMENTS_PER_REGISTRATION,
)


class ResearcherApplicationForm(forms.Form):
    email = forms.EmailField(label="Institutional or work email")
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput,
        strip=False,
        help_text="Use a unique password. Researcher access stays disabled until staff approval.",
    )
    password2 = forms.CharField(
        label="Confirm password",
        widget=forms.PasswordInput,
        strip=False,
    )
    applicant_type = forms.ChoiceField(choices=ResearcherApplication.ApplicantType.choices)
    organisation_name = forms.CharField(max_length=200)
    role_title = forms.CharField(max_length=120, required=False)
    phone = forms.CharField(max_length=32)
    website = forms.URLField(required=False)
    country = forms.CharField(max_length=100, initial="Kenya")
    supervisor_name = forms.CharField(max_length=160, required=False)
    supervisor_email = forms.EmailField(required=False)
    research_purpose = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 4}),
        help_text="What research will you conduct and what decisions may it inform?",
    )
    methods_summary = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 4}),
        help_text="Describe recruitment, data handling, ethics review, and how findings will be used.",
    )
    privacy_policy_url = forms.URLField(required=False)
    data_protection_contact = forms.CharField(max_length=200, required=False)
    consent = forms.BooleanField(
        label=(
            "I agree to MoFirms reviewing this application and contacting me about vetting. "
            "I understand that approval is manual and does not provide customer data access."
        )
    )

    def __init__(self, *args, lang="en", **kwargs):
        super().__init__(*args, **kwargs)
        self.lang = lang
        self.fields["email"].label = translate("field.researcher.email", lang)
        self.fields["password1"].label = translate("field.researcher.password1", lang)
        self.fields["password1"].help_text = translate("help.researcher.password1", lang)
        self.fields["password2"].label = translate("field.researcher.password2", lang)
        self.fields["applicant_type"].choices = localize_choices(
            ResearcherApplication.ApplicantType.choices, lang, "choice.researcher_applicant_type"
        )
        self.fields["research_purpose"].help_text = translate(
            "help.researcher.research_purpose", lang
        )
        self.fields["methods_summary"].help_text = translate(
            "help.researcher.methods_summary", lang
        )
        self.fields["consent"].label = translate("field.researcher.consent", lang)

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        user_model = get_user_model()
        if (
            user_model.objects.filter(email__iexact=email).exists()
            or user_model.objects.filter(username__iexact=email).exists()
        ):
            raise ValidationError(translate("err.researcher.email_taken", self.lang))
        return email

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            self.add_error("password2", translate("err.researcher.passwords_mismatch", self.lang))

        if (
            cleaned_data.get("applicant_type") == ResearcherApplication.ApplicantType.STUDENT
            and not cleaned_data.get("supervisor_name")
        ):
            self.add_error("supervisor_name", translate("err.researcher.supervisor_name_required", self.lang))
        if (
            cleaned_data.get("applicant_type") == ResearcherApplication.ApplicantType.STUDENT
            and not cleaned_data.get("supervisor_email")
        ):
            self.add_error("supervisor_email", translate("err.researcher.supervisor_email_required", self.lang))
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")
        email = cleaned_data.get("email")
        if password1 and password1 == password2 and email:
            user_model = get_user_model()
            user = user_model(username=email, email=email)
            try:
                validate_password(password1, user)
            except ValidationError as error:
                self.add_error("password1", error)
        return cleaned_data

class ResearchStudyForm(forms.ModelForm):
    target_audiences = forms.MultipleChoiceField(
        choices=ResearchStudy.Audience.choices,
        widget=forms.CheckboxSelectMultiple,
        label="Which MoFirms registrant categories are in scope?",
    )
    target_counties = forms.MultipleChoiceField(
        choices=[(county, county) for county in COUNTIES],
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Target counties (optional)",
    )

    class Meta:
        model = ResearchStudy
        fields = [
            "title",
            "purpose",
            "intended_use",
            "methodology",
            "target_audiences",
            "target_counties",
            "target_sample_size",
            "ethics_status",
            "ethics_body",
            "ethics_reference",
            "respondent_consent_text",
            "closes_at",
        ]
        widgets = {
            "purpose": forms.Textarea(attrs={"rows": 3}),
            "intended_use": forms.Textarea(attrs={"rows": 3}),
            "methodology": forms.Textarea(attrs={"rows": 3}),
            "respondent_consent_text": forms.Textarea(attrs={"rows": 4, "maxlength": "1000"}),
            "closes_at": forms.DateTimeInput(
                attrs={"type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
        }
        help_texts = {
            "target_sample_size": "A planning estimate only; MoFirms does not promise a response count.",
            "respondent_consent_text": (
                "Explain purpose, voluntary participation, expected time, use and retention. "
                "Do not promise anonymity beyond what the study actually provides."
            ),
            "ethics_reference": "Do not upload ethics documents containing participant data.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["closes_at"].input_formats = ["%Y-%m-%dT%H:%M"]

    def save(self, commit=True):
        study = super().save(commit=False)
        study.target_audiences = self.cleaned_data["target_audiences"]
        study.target_counties = self.cleaned_data["target_counties"]
        if commit:
            study.save()
        return study


class ResearchQuestionForm(forms.Form):
    prompt = forms.CharField(
        max_length=240,
        label="Question",
        widget=forms.TextInput(attrs={"maxlength": "240"}),
    )
    answer_type = forms.ChoiceField(choices=ResearchQuestion.AnswerType.choices)
    options_text = forms.CharField(
        label="Answer options (one per line)",
        widget=forms.Textarea(attrs={"rows": 4}),
        help_text="Provide 2–8 short options. Do not use free-text answer questions.",
    )
    required = forms.BooleanField(
        required=False,
        label="Require respondents to answer",
    )

    def clean_options_text(self):
        options = [option.strip() for option in self.cleaned_data["options_text"].splitlines()]
        options = [option for option in options if option]
        if not 2 <= len(options) <= 8:
            raise ValidationError("Each question needs between 2 and 8 answer options.")
        normalized = [option.casefold() for option in options]
        if len(normalized) != len(set(normalized)):
            raise ValidationError("Answer options must be unique.")
        if any(len(option) > 80 for option in options):
            raise ValidationError("Each answer option must be 80 characters or fewer.")
        return options

    def save(self, study, position):
        return ResearchQuestion.objects.create(
            study=study,
            position=position,
            prompt=self.cleaned_data["prompt"],
            answer_type=self.cleaned_data["answer_type"],
            options=self.cleaned_data["options_text"],
            required=self.cleaned_data["required"],
        )


ResearchQuestionFormSet = formset_factory(
    ResearchQuestionForm,
    extra=1,
    min_num=1,
    max_num=12,
    validate_min=True,
    validate_max=True,
    absolute_max=12,
)


class ConsultationLeadForm(forms.ModelForm):
    privacy_consent = forms.BooleanField(
        required=True,
        label="I agree that MoFirms may use these details to respond to my consultation request.",
    )
    website = forms.CharField(required=False, widget=forms.HiddenInput)

    def __init__(self, *args, lang="en", **kwargs):
        super().__init__(*args, **kwargs)
        self.lang = lang
        self.fields["privacy_consent"].label = translate("field.consultation.privacy_consent", lang)
        self.fields["preferred_contact"].choices = localize_choices(
            ConsultationLead.PreferredContact.choices, lang, "choice.preferred_contact_short"
        )
        self.fields["category"].choices = localize_choices(
            ConsultationLead.Category.choices, lang, "choice.consultation_category"
        )

    class Meta:
        model = ConsultationLead
        fields = (
            "full_name",
            "preferred_contact",
            "email",
            "phone",
            "organisation_or_county",
            "category",
            "message",
        )
        widgets = {
            "full_name": forms.TextInput(attrs={"id": "name", "autocomplete": "name"}),
            "preferred_contact": forms.Select(attrs={"id": "how"}),
            "email": forms.EmailInput(attrs={"id": "email", "autocomplete": "email"}),
            "phone": forms.TextInput(
                attrs={"id": "phone", "type": "tel", "autocomplete": "tel"}
            ),
            "organisation_or_county": forms.TextInput(attrs={"id": "org"}),
            "category": forms.Select(attrs={"id": "cat"}),
            "message": forms.Textarea(attrs={"id": "msg", "rows": 3, "maxlength": 1200}),
        }

    def clean_website(self):
        website = self.cleaned_data["website"]
        if website:
            raise ValidationError(translate("err.honeypot.unable_to_submit", self.lang))
        return website


class NewsletterSubscriptionForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={"autocomplete": "email", "placeholder": "you@example.com"}
        ),
    )
    topics = forms.MultipleChoiceField(
        choices=NewsletterSubscription.Topic.choices,
        required=True,
        widget=forms.CheckboxSelectMultiple,
        label="Choose the updates you want",
    )
    marketing_consent = forms.BooleanField(
        required=True,
        label="I agree to receive the MoFirms newsletter by email about the topics selected. I can unsubscribe at any time.",
    )
    website = forms.CharField(required=False, widget=forms.HiddenInput)

    def __init__(self, *args, lang="en", **kwargs):
        super().__init__(*args, **kwargs)
        self.lang = lang
        self.fields["topics"].label = translate("field.newsletter.topics", lang)
        self.fields["topics"].choices = localize_choices(
            NewsletterSubscription.Topic.choices, lang, "choice.newsletter_topic"
        )
        self.fields["marketing_consent"].label = translate(
            "field.newsletter.marketing_consent", lang
        )

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()

    def clean_website(self):
        website = self.cleaned_data["website"]
        if website:
            raise ValidationError(translate("err.honeypot.unable_to_submit", self.lang))
        return website


class ResearchResponseForm(forms.Form):
    participant_consent = forms.BooleanField(
        label="I have read the study information and freely choose to participate."
    )

    def __init__(self, *args, questions, **kwargs):
        super().__init__(*args, **kwargs)
        self.questions = list(questions)
        for question in self.questions:
            choices = [(option, option) for option in question.options]
            field_name = f"question_{question.pk}"
            if question.answer_type == ResearchQuestion.AnswerType.MULTIPLE:
                self.fields[field_name] = forms.MultipleChoiceField(
                    choices=choices,
                    required=question.required,
                    widget=forms.CheckboxSelectMultiple,
                    label=question.prompt,
                )
            else:
                self.fields[field_name] = forms.ChoiceField(
                    choices=choices,
                    required=question.required,
                    widget=forms.RadioSelect,
                    label=question.prompt,
                )

    def response_answers(self):
        return {
            str(question.pk): self.cleaned_data.get(f"question_{question.pk}", [])
            for question in self.questions
        }


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
