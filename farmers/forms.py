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
    SUPPORT_CHOICES,
    FarmerDocument,
    FarmerProfile,
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
        label="Choose a PDF, JPG, or PNG (maximum 5 MB)",
        widget=forms.ClearableFileInput(attrs={"accept": ".pdf,.jpg,.jpeg,.png"}),
    )

    def clean_file(self):
        uploaded = self.cleaned_data["file"]
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
                logger.warning(
                    "A farmer registration upload was rejected by the malware scanner."
                )
                raise ValidationError(
                    "The evidence could not be accepted. Check the file and try again."
                )
        return uploaded


FarmerDocumentFormSet = formset_factory(
    FarmerDocumentForm,
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
