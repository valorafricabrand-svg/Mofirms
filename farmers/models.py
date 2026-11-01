import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


COUNTIES = (
    "Baringo", "Bomet", "Bungoma", "Busia", "Elgeyo-Marakwet", "Embu",
    "Garissa", "Homa Bay", "Isiolo", "Kajiado", "Kakamega", "Kericho",
    "Kiambu", "Kilifi", "Kirinyaga", "Kisii", "Kisumu", "Kitui", "Kwale",
    "Laikipia", "Lamu", "Machakos", "Makueni", "Mandera", "Marsabit",
    "Meru", "Migori", "Mombasa", "Murang'a", "Nairobi City", "Nakuru",
    "Nandi", "Narok", "Nyamira", "Nyandarua", "Nyeri", "Samburu",
    "Siaya", "Taita-Taveta", "Tana River", "Tharaka-Nithi", "Trans Nzoia",
    "Turkana", "Uasin Gishu", "Vihiga", "Wajir", "West Pokot",
)

ACTIVITY_CHOICES = (
    ("crops", "Crops"),
    ("livestock", "Livestock"),
    ("dairy", "Dairy"),
    ("poultry", "Poultry"),
    ("horticulture", "Horticulture"),
    ("beekeeping", "Beekeeping"),
    ("fisheries", "Fisheries"),
    ("agroforestry", "Agroforestry"),
    ("other", "Other"),
)

SUPPORT_CHOICES = (
    ("farm_planning", "Farm or production planning"),
    ("training", "Training and capacity building"),
    ("markets", "Market access and buyers"),
    ("business_planning", "Business planning"),
    ("finance_readiness", "Finance readiness"),
    ("bookkeeping", "Bookkeeping and business records"),
    ("digital_tools", "Digital tools and data"),
    ("climate", "Climate resilience"),
    ("other", "Other or not sure yet"),
)


class FarmerProfile(models.Model):
    class RegistrationType(models.TextChoices):
        INDIVIDUAL = "individual", "Individual farmer"
        GROUP = "group", "Farmer group or association"

    class GroupType(models.TextChoices):
        FARMER_GROUP = "farmer_group", "Farmer group"
        SELF_HELP = "self_help", "Self-help group"
        COOPERATIVE = "cooperative", "Cooperative"
        ASSOCIATION = "association", "Association"
        PRODUCER_ORGANISATION = "producer_organisation", "Producer organisation"
        OTHER = "other", "Other"

    class RegistrationStatus(models.TextChoices):
        REGISTERED = "registered", "Registered"
        IN_PROGRESS = "in_progress", "Registration in progress"
        NOT_REGISTERED = "not_registered", "Not registered"
        NOT_APPLICABLE = "not_applicable", "Not applicable"
        PREFER_NOT = "prefer_not", "Prefer not to say"

    class VerificationStatus(models.TextChoices):
        PENDING = "pending", "Pending review"
        IN_REVIEW = "in_review", "In review"
        VERIFIED = "verified", "Verified by MoFirms reviewer"
        FOLLOW_UP = "follow_up", "Needs follow-up"
        NOT_VERIFIED = "not_verified", "Not verified"

    class EvidenceStatus(models.TextChoices):
        PENDING = "pending", "Pending review"
        IN_REVIEW = "in_review", "In review"
        VERIFIED = "verified", "Verified by MoFirms reviewer"
        FOLLOW_UP = "follow_up", "Needs follow-up"
        NOT_VERIFIED = "not_verified", "Not verified"
        NOT_APPLICABLE = "not_applicable", "Not applicable"

    class ContactPreference(models.TextChoices):
        PHONE = "phone", "Phone or SMS"
        WHATSAPP = "whatsapp", "WhatsApp"
        EMAIL = "email", "Email"

    class LandAccess(models.TextChoices):
        OWNED = "owned", "Owned by farmer or members"
        LEASED = "leased", "Leased or rented"
        FAMILY_COMMUNITY = "family_community", "Family or community land"
        OTHER = "other", "Other arrangement"
        PREFER_NOT = "prefer_not", "Prefer not to say"

    class AreaUnit(models.TextChoices):
        ACRES = "acres", "Acres"
        HECTARES = "hectares", "Hectares"

    class WaterSource(models.TextChoices):
        RAINFED = "rainfed", "Rain-fed"
        RIVER = "river", "River or stream"
        BOREHOLE = "borehole", "Borehole or well"
        PIPED = "piped", "Piped supply"
        HARVESTING = "harvesting", "Rainwater harvesting"
        OTHER = "other", "Other"

    class RecordKeeping(models.TextChoices):
        NONE = "none", "No regular written records"
        PAPER = "paper", "Paper records"
        DIGITAL = "digital", "Digital records"
        BOTH = "both", "Paper and digital records"
        PREFER_NOT = "prefer_not", "Prefer not to say"

    class FinancialBand(models.TextChoices):
        NONE = "none", "None or not applicable"
        UNDER_100K = "under_100k", "Under KSh 100,000"
        RANGE_100_500K = "100_500k", "KSh 100,000–500,000"
        RANGE_500K_2M = "500k_2m", "KSh 500,001–2,000,000"
        RANGE_2_10M = "2_10m", "KSh 2,000,001–10,000,000"
        OVER_10M = "over_10m", "Over KSh 10,000,000"
        PREFER_NOT = "prefer_not", "Prefer not to say"

    class Experience(models.TextChoices):
        UNDER_1 = "under_1", "Less than 1 year"
        ONE_TO_3 = "1_3", "1–3 years"
        FOUR_TO_10 = "4_10", "4–10 years"
        OVER_10 = "over_10", "More than 10 years"
        PREFER_NOT = "prefer_not", "Prefer not to say"

    reference = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    registration_type = models.CharField(max_length=16, choices=RegistrationType.choices)
    full_name = models.CharField(max_length=160)
    phone = models.CharField(max_length=32, blank=True)
    email = models.EmailField(blank=True)
    preferred_contact = models.CharField(max_length=12, choices=ContactPreference.choices)
    preferred_language = models.CharField(max_length=32, blank=True)

    group_name = models.CharField(max_length=180, blank=True)
    group_type = models.CharField(max_length=32, choices=GroupType.choices, blank=True)
    group_registration_status = models.CharField(
        max_length=24, choices=RegistrationStatus.choices,
        default=RegistrationStatus.NOT_APPLICABLE,
    )
    group_registration_number = models.CharField(max_length=80, blank=True)
    group_member_count = models.PositiveIntegerField(null=True, blank=True)
    representative_role = models.CharField(max_length=100, blank=True)
    group_authorization_confirmed = models.BooleanField(default=False)

    county = models.CharField(max_length=32, choices=[(county, county) for county in COUNTIES])
    sub_county = models.CharField(max_length=100, blank=True)
    ward = models.CharField(max_length=100, blank=True)
    local_area = models.CharField(max_length=120, blank=True)

    activities = models.JSONField(default=list, blank=True)
    main_products = models.CharField(max_length=300, blank=True)
    farm_size = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(1_000_000)],
    )
    farm_size_unit = models.CharField(max_length=10, choices=AreaUnit.choices, blank=True)
    land_access = models.CharField(max_length=20, choices=LandAccess.choices, blank=True)
    years_farming = models.CharField(max_length=12, choices=Experience.choices, blank=True)
    water_sources = models.JSONField(default=list, blank=True)
    production_summary = models.TextField(blank=True)
    sales_band = models.CharField(max_length=16, choices=FinancialBand.choices, blank=True)
    operating_cost_band = models.CharField(max_length=16, choices=FinancialBand.choices, blank=True)
    finance_need_band = models.CharField(max_length=16, choices=FinancialBand.choices, blank=True)
    record_keeping = models.CharField(max_length=16, choices=RecordKeeping.choices, blank=True)
    sales_channels = models.JSONField(default=list, blank=True)
    challenges = models.JSONField(default=list, blank=True)
    support_interests = models.JSONField(default=list, blank=True)
    goals = models.TextField(blank=True)
    additional_notes = models.TextField(blank=True)

    verification_status = models.CharField(
        max_length=16, choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING,
    )
    identity_review_status = models.CharField(
        max_length=16, choices=EvidenceStatus.choices,
        default=EvidenceStatus.PENDING,
    )
    group_review_status = models.CharField(
        max_length=16, choices=EvidenceStatus.choices,
        default=EvidenceStatus.NOT_APPLICABLE,
    )
    farm_review_status = models.CharField(
        max_length=16, choices=EvidenceStatus.choices,
        default=EvidenceStatus.PENDING,
    )
    verification_notes = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_farmer_profiles",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    privacy_consent_at = models.DateTimeField()
    document_consent_at = models.DateTimeField(null=True, blank=True)
    privacy_policy_version = models.CharField(max_length=24, default="2026-11-01")
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)
    last_contact_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "farmer registration"
        verbose_name_plural = "farmer registrations"

    def __str__(self):
        if self.registration_type == self.RegistrationType.GROUP and self.group_name:
            return f"{self.group_name} ({self.full_name})"
        return f"{self.full_name} ({self.get_county_display()})"

    def clean(self):
        super().clean()
        if self.registration_type == self.RegistrationType.GROUP:
            if self.group_review_status == self.EvidenceStatus.NOT_APPLICABLE:
                raise ValidationError(
                    {"group_review_status": "Group registrations require a group review status."}
                )
            if not self.group_authorization_confirmed:
                raise ValidationError(
                    {"group_authorization_confirmed": "Group representative authorisation must be confirmed."}
                )
        elif self.group_review_status != self.EvidenceStatus.NOT_APPLICABLE:
            self.group_review_status = self.EvidenceStatus.NOT_APPLICABLE
        if self.verification_status == self.VerificationStatus.VERIFIED and not self.verification_notes.strip():
            raise ValidationError(
                {"verification_notes": "Add the basis and scope before marking the registration verified."}
            )

    @property
    def public_reference(self):
        return str(self.reference).split("-")[0].upper()


def private_document_path(instance, filename):
    suffix = filename.rsplit(".", 1)[-1].lower()
    return f"{instance.profile.reference}/{instance.reference}.{suffix}"


class FarmerDocument(models.Model):
    class DocumentType(models.TextChoices):
        IDENTITY = "identity", "Individual identity evidence"
        GROUP = "group", "Group registration or governance evidence"
        FARM = "farm", "Farm activity or production evidence"
        OTHER = "other", "Other relevant evidence"

    class ReviewStatus(models.TextChoices):
        PENDING = "pending", "Pending review"
        ACCEPTED = "accepted", "Evidence reviewed"
        FOLLOW_UP = "follow_up", "Follow-up required"
        NOT_ACCEPTED = "not_accepted", "Not accepted"

    reference = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    profile = models.ForeignKey(
        FarmerProfile, on_delete=models.CASCADE, related_name="documents"
    )
    document_type = models.CharField(max_length=16, choices=DocumentType.choices)
    description = models.CharField(max_length=200, blank=True)
    file = models.FileField(upload_to=private_document_path)
    review_status = models.CharField(
        max_length=16, choices=ReviewStatus.choices, default=ReviewStatus.PENDING
    )
    review_notes = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_farmer_documents",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    uploaded_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        ordering = ["uploaded_at"]

    def __str__(self):
        return f"{self.get_document_type_display()} — {self.profile}"

    def clean(self):
        super().clean()
        if (
            self.review_status == self.ReviewStatus.ACCEPTED
            and not self.review_notes.strip()
        ):
            raise ValidationError(
                {"review_notes": "Record what evidence was reviewed before accepting this document."}
            )
