import uuid
from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone


def default_beta_invite_expiry():
    return timezone.now() + timedelta(days=30)


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

PARTNER_ROLE_CHOICES = (
    ("supplier", "Input or service supplier"),
    ("buyer", "Produce buyer"),
    ("service_provider", "Professional or technical service provider"),
)

PARTNER_OFFER_CHOICES = (
    ("seeds_seedlings", "Seeds and seedlings"),
    ("fertilizer_soil", "Fertilizers, soil health, and crop inputs"),
    ("crop_protection", "Crop protection products"),
    ("farm_tools", "Farm tools and equipment"),
    ("irrigation", "Irrigation and water systems"),
    ("livestock_inputs", "Livestock feed and animal health"),
    ("poultry_inputs", "Poultry inputs and equipment"),
    ("beekeeping", "Beekeeping inputs and equipment"),
    ("machinery", "Farm machinery and mechanisation"),
    ("storage_processing", "Storage and processing"),
    ("packaging", "Packaging and post-harvest handling"),
    ("transport", "Transport and logistics"),
    ("digital", "Digital and farm technology"),
    ("training", "Training and capacity building"),
    ("consulting", "Agribusiness advisory and consulting"),
    ("financial", "Finance and business support"),
    ("veterinary", "Veterinary and animal-health services"),
    ("environmental", "Environmental and climate services"),
    ("other", "Other goods or services"),
)

PRODUCE_CATEGORY_CHOICES = (
    ("cereals", "Cereals and grains"),
    ("legumes", "Beans, peas, and pulses"),
    ("roots", "Roots and tubers"),
    ("vegetables", "Vegetables"),
    ("fruits", "Fruits"),
    ("dairy", "Milk and dairy"),
    ("livestock", "Live animals and meat"),
    ("poultry", "Eggs and poultry"),
    ("fish", "Fish and aquaculture"),
    ("honey", "Honey and bee products"),
    ("oilseeds", "Oilseeds and oil crops"),
    ("other", "Other produce"),
)

PARTNER_DELIVERY_CHOICES = (
    ("collection_point", "Buyer or supplier collection point"),
    ("farm_gate", "Farm-gate collection or delivery"),
    ("county_delivery", "Delivery within a county"),
    ("multi_county", "Multi-county delivery or collection"),
    ("national", "National delivery or collection"),
    ("online", "Online or remote service"),
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

    county = models.CharField(
        max_length=32, choices=[(county, county) for county in COUNTIES], blank=True,
    )
    sub_county = models.CharField(max_length=100, blank=True)
    ward = models.CharField(max_length=100, blank=True)
    local_area = models.CharField(max_length=120, blank=True)
    farm_latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True,
        help_text="Received from a WhatsApp location share; not entered on the web form.",
    )
    farm_longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True,
    )
    location_shared_at = models.DateTimeField(null=True, blank=True)

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
    research_invite_consent_at = models.DateTimeField(null=True, blank=True)
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
        if self.county:
            return f"{self.full_name} ({self.get_county_display()})"
        return self.full_name

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


class WhatsAppLocationPing(models.Model):
    """A raw location share received from Meta's WhatsApp webhook, matched to a
    farmer registration by phone number where possible. Kept as an immutable log
    even after matching, so staff can audit what was actually received."""

    wa_message_id = models.CharField(max_length=128, unique=True)
    phone_number = models.CharField(max_length=32)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    received_at = models.DateTimeField(default=timezone.now, editable=False)
    matched_profile = models.ForeignKey(
        FarmerProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="whatsapp_location_pings",
    )

    class Meta:
        ordering = ["-received_at"]

    def __str__(self):
        return f"Location from {self.phone_number} at {self.received_at:%Y-%m-%d %H:%M}"


class PartnerProfile(models.Model):
    class ApplicantType(models.TextChoices):
        INDIVIDUAL = "individual", "Individual or sole proprietor"
        BUSINESS = "business", "Registered or unregistered organisation"

    class RegistrationStatus(models.TextChoices):
        REGISTERED = "registered", "Registered"
        IN_PROGRESS = "in_progress", "Registration in progress"
        NOT_REGISTERED = "not_registered", "Not registered"
        PREFER_NOT = "prefer_not", "Prefer not to say"

    class ContactPreference(models.TextChoices):
        PHONE = "phone", "Phone or SMS"
        WHATSAPP = "whatsapp", "WhatsApp"
        EMAIL = "email", "Email"

    class ReviewStatus(models.TextChoices):
        PENDING = "pending", "Pending review"
        IN_REVIEW = "in_review", "In review"
        VERIFIED = "verified", "Verified by MoFirms reviewer"
        FOLLOW_UP = "follow_up", "Needs follow-up"
        NOT_VERIFIED = "not_verified", "Not verified"
        NOT_APPLICABLE = "not_applicable", "Not applicable"

    class CapacityBand(models.TextChoices):
        STARTING = "starting", "New or pilot capacity"
        SMALL = "small", "Small or local capacity"
        MEDIUM = "medium", "Growing or multi-county capacity"
        LARGE = "large", "Large or national capacity"
        VARIABLE = "variable", "Varies by season or contract"
        PREFER_NOT = "prefer_not", "Prefer not to say"

    class BusinessSize(models.TextChoices):
        MICRO = "micro", "Micro or sole operator"
        SMALL = "small", "Small business"
        MEDIUM = "medium", "Medium business"
        LARGE = "large", "Large business"
        COOPERATIVE = "cooperative", "Cooperative or member organisation"
        PREFER_NOT = "prefer_not", "Prefer not to say"

    class StaffBand(models.TextChoices):
        SOLO = "solo", "Sole operator"
        TWO_TO_5 = "2_5", "2–5 people"
        SIX_TO_20 = "6_20", "6–20 people"
        TWENTY_ONE_TO_50 = "21_50", "21–50 people"
        OVER_50 = "over_50", "More than 50 people"
        PREFER_NOT = "prefer_not", "Prefer not to say"

    class Experience(models.TextChoices):
        UNDER_1 = "under_1", "Less than 1 year"
        ONE_TO_3 = "1_3", "1–3 years"
        FOUR_TO_10 = "4_10", "4–10 years"
        OVER_10 = "over_10", "More than 10 years"
        PREFER_NOT = "prefer_not", "Prefer not to say"

    reference = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    applicant_type = models.CharField(max_length=16, choices=ApplicantType.choices)
    contact_name = models.CharField(max_length=160)
    business_name = models.CharField(max_length=180, blank=True)
    trading_name = models.CharField(max_length=180, blank=True)
    business_description = models.TextField(blank=True)
    phone = models.CharField(max_length=32, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)
    preferred_contact = models.CharField(max_length=12, choices=ContactPreference.choices)
    preferred_language = models.CharField(max_length=32, blank=True)

    registration_status = models.CharField(
        max_length=16,
        choices=RegistrationStatus.choices,
        default=RegistrationStatus.NOT_REGISTERED,
    )
    registration_number = models.CharField(
        max_length=100,
        blank=True,
        help_text="Business or organisation registration number only; do not enter a personal ID or tax PIN.",
    )
    year_established = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=[MinValueValidator(1800), MaxValueValidator(2100)]
    )
    years_experience = models.CharField(max_length=12, choices=Experience.choices, blank=True)
    business_size = models.CharField(max_length=12, choices=BusinessSize.choices, blank=True)
    staff_band = models.CharField(max_length=12, choices=StaffBand.choices, blank=True)
    roles = models.JSONField(default=list)

    county = models.CharField(max_length=32, choices=[(county, county) for county in COUNTIES])
    sub_county = models.CharField(max_length=100, blank=True)
    ward = models.CharField(max_length=100, blank=True)
    operating_counties = models.JSONField(default=list, blank=True)
    delivery_methods = models.JSONField(default=list, blank=True)

    offer_categories = models.JSONField(default=list, blank=True)
    offer_details = models.TextField(blank=True)
    service_description = models.TextField(blank=True)
    brands_or_products = models.CharField(max_length=300, blank=True)
    service_area = models.CharField(max_length=200, blank=True)
    lead_time = models.CharField(max_length=100, blank=True)
    minimum_order = models.CharField(max_length=100, blank=True)
    prices_and_terms = models.TextField(blank=True)

    produce_categories = models.JSONField(default=list, blank=True)
    produce_details = models.TextField(blank=True)
    sourcing_counties = models.JSONField(default=list, blank=True)
    buyer_capacity = models.CharField(max_length=12, choices=CapacityBand.choices, blank=True)
    buying_frequency = models.CharField(max_length=100, blank=True)
    quality_requirements = models.TextField(blank=True)
    payment_terms = models.CharField(max_length=200, blank=True)

    clients_and_references = models.TextField(blank=True)
    licences_and_standards = models.TextField(blank=True)
    service_capacity = models.CharField(max_length=12, choices=CapacityBand.choices, blank=True)
    staff_qualifications = models.TextField(blank=True)
    engagement_interests = models.JSONField(default=list, blank=True)

    challenges = models.JSONField(default=list, blank=True)
    partnership_goals = models.TextField(blank=True)
    additional_notes = models.TextField(blank=True)
    contact_consent_at = models.DateTimeField()
    listing_referral_consent_at = models.DateTimeField(null=True, blank=True)
    research_invite_consent_at = models.DateTimeField(null=True, blank=True)
    document_consent_at = models.DateTimeField(null=True, blank=True)
    privacy_policy_version = models.CharField(max_length=24, default="2026-11-01")
    verification_status = models.CharField(
        max_length=16, choices=ReviewStatus.choices, default=ReviewStatus.PENDING
    )
    identity_review_status = models.CharField(
        max_length=16, choices=ReviewStatus.choices, default=ReviewStatus.PENDING
    )
    business_review_status = models.CharField(
        max_length=16, choices=ReviewStatus.choices, default=ReviewStatus.PENDING
    )
    offering_review_status = models.CharField(
        max_length=16, choices=ReviewStatus.choices, default=ReviewStatus.PENDING
    )
    verification_notes = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_partner_profiles",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)
    last_contact_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "supplier and buyer registration"
        verbose_name_plural = "supplier and buyer registrations"

    def __str__(self):
        return self.business_name or self.trading_name or self.contact_name

    @property
    def public_reference(self):
        return str(self.reference).split("-")[0].upper()

    def clean(self):
        super().clean()
        if not self.roles:
            raise ValidationError({"roles": "Select at least one partner role."})
        valid_roles = {choice[0] for choice in PARTNER_ROLE_CHOICES}
        if not set(self.roles).issubset(valid_roles):
            raise ValidationError({"roles": "One or more selected partner roles are invalid."})
        if (
            self.applicant_type == self.ApplicantType.BUSINESS
            and not self.business_name.strip()
        ):
            raise ValidationError({"business_name": "Enter the organisation or business name."})
        if (
            self.preferred_contact == self.ContactPreference.EMAIL
            and not self.email.strip()
        ):
            raise ValidationError({"email": "An email is required for the selected contact method."})
        if (
            self.preferred_contact in {self.ContactPreference.PHONE, self.ContactPreference.WHATSAPP}
            and not self.phone.strip()
        ):
            raise ValidationError({"phone": "A phone number is required for the selected contact method."})
        if (
            self.verification_status == self.ReviewStatus.VERIFIED
            and not self.verification_notes.strip()
        ):
            raise ValidationError(
                {"verification_notes": "Document the evidence and scope of verification before approval."}
            )


def private_partner_document_path(instance, filename):
    suffix = filename.rsplit(".", 1)[-1].lower()
    return f"partners/{instance.profile.reference}/{instance.reference}.{suffix}"


class PartnerDocument(models.Model):
    class DocumentType(models.TextChoices):
        IDENTITY = "identity", "Identity evidence for individual contact"
        BUSINESS = "business", "Business or organisation registration"
        AUTHORITY = "authority", "Representative authorisation"
        PROFESSIONAL = "professional", "Professional qualification or licence"
        PRODUCT = "product", "Product catalogue or specification"
        QUALITY = "quality", "Quality, safety, or standards evidence"
        REFERENCES = "references", "Service or trade references"
        CAPACITY = "capacity", "Supply or buying capacity evidence"
        OTHER = "other", "Other relevant evidence"

    class ReviewStatus(models.TextChoices):
        PENDING = "pending", "Pending review"
        ACCEPTED = "accepted", "Evidence reviewed"
        FOLLOW_UP = "follow_up", "Follow-up required"
        NOT_ACCEPTED = "not_accepted", "Not accepted"

    reference = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    profile = models.ForeignKey(
        PartnerProfile, on_delete=models.CASCADE, related_name="documents"
    )
    document_type = models.CharField(max_length=16, choices=DocumentType.choices)
    description = models.CharField(max_length=200, blank=True)
    file = models.FileField(upload_to=private_partner_document_path)
    review_status = models.CharField(
        max_length=16, choices=ReviewStatus.choices, default=ReviewStatus.PENDING
    )
    review_notes = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_partner_documents",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    uploaded_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        ordering = ["uploaded_at"]

    def __str__(self):
        return f"{self.get_document_type_display()} — {self.profile}"

    def clean(self):
        super().clean()
        if self.review_status == self.ReviewStatus.ACCEPTED and not self.review_notes.strip():
            raise ValidationError(
                {"review_notes": "Record what evidence was reviewed before accepting this document."}
            )


def private_financial_analysis_document_path(instance, filename):
    suffix = filename.rsplit(".", 1)[-1].lower() if "." in filename else "bin"
    return f"financial-analysis/{instance.request.reference}/{uuid.uuid4()}.{suffix}"


class FinancialAnalysisRequest(models.Model):
    class RequestType(models.TextChoices):
        GENERAL = "general", "Financial analysis request"
        BUSINESS_READINESS = "business_readiness", "Business readiness pilot"

    class ApplicantType(models.TextChoices):
        INDIVIDUAL = "individual", "Individual or sole proprietor"
        BUSINESS = "business", "Business, group, or organisation"

    class ContactPreference(models.TextChoices):
        PHONE = "phone", "Phone or SMS"
        WHATSAPP = "whatsapp", "WhatsApp"
        EMAIL = "email", "Email"

    class ServiceStatus(models.TextChoices):
        PENDING = "pending", "New request"
        IN_REVIEW = "in_review", "Under initial review"
        NEEDS_INFORMATION = "needs_information", "More information requested"
        QUOTED = "quoted", "Quote sent"
        ACCEPTED = "accepted", "Quote accepted"
        IN_PROGRESS = "in_progress", "Analysis in progress"
        COMPLETED = "completed", "Completed"
        DECLINED = "declined", "Not proceeding"
        CANCELLED = "cancelled", "Cancelled"

    class RevenueBand(models.TextChoices):
        PRE_REVENUE = "pre_revenue", "Not yet generating revenue"
        UNDER_500K = "under_500k", "Under KSh 500,000 per year"
        FROM_500K_TO_2M = "500k_2m", "KSh 500,000–2 million per year"
        FROM_2M_TO_10M = "2m_10m", "KSh 2–10 million per year"
        OVER_10M = "over_10m", "Over KSh 10 million per year"
        PREFER_NOT = "prefer_not", "Prefer not to say"

    class FundingNeedBand(models.TextChoices):
        NONE = "none", "No funding request"
        UNDER_500K = "under_500k", "Under KSh 500,000"
        FROM_500K_TO_2M = "500k_2m", "KSh 500,000–2 million"
        FROM_2M_TO_10M = "2m_10m", "KSh 2–10 million"
        OVER_10M = "over_10m", "Over KSh 10 million"
        PREFER_NOT = "prefer_not", "Prefer not to say"

    class Timeline(models.TextChoices):
        ASAP = "asap", "As soon as practical"
        TWO_WEEKS = "two_weeks", "Within two weeks"
        MONTH = "month", "Within one month"
        FLEXIBLE = "flexible", "Flexible"

    class ReviewStatus(models.TextChoices):
        PENDING = "pending", "Pending review"
        IN_REVIEW = "in_review", "In review"
        ACCEPTED = "accepted", "Records reviewed"
        FOLLOW_UP = "follow_up", "Needs follow-up"
        NOT_ACCEPTED = "not_accepted", "Not accepted"
        NOT_APPLICABLE = "not_applicable", "Not applicable"

    reference = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    request_type = models.CharField(
        max_length=24,
        choices=RequestType.choices,
        default=RequestType.GENERAL,
    )
    applicant_type = models.CharField(max_length=16, choices=ApplicantType.choices)
    contact_name = models.CharField(max_length=160)
    business_name = models.CharField(max_length=180, blank=True)
    phone = models.CharField(max_length=32, blank=True)
    email = models.EmailField(blank=True)
    preferred_contact = models.CharField(max_length=12, choices=ContactPreference.choices)
    county = models.CharField(max_length=32, choices=[(county, county) for county in COUNTIES])
    sector = models.CharField(max_length=120, blank=True)
    business_goal = models.TextField(blank=True)
    current_challenge = models.TextField(blank=True)
    average_monthly_sales = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )
    average_monthly_costs = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )
    seasonality_notes = models.CharField(max_length=500, blank=True)
    services_requested = models.JSONField(default=list)
    financial_period = models.CharField(max_length=100, blank=True)
    records_available = models.JSONField(default=list, blank=True)
    accounting_software = models.CharField(max_length=120, blank=True)
    annual_revenue_band = models.CharField(max_length=16, choices=RevenueBand.choices, blank=True)
    funding_need_band = models.CharField(max_length=16, choices=FundingNeedBand.choices, blank=True)
    timeline = models.CharField(max_length=16, choices=Timeline.choices, blank=True)
    request_summary = models.TextField()
    contact_consent_at = models.DateTimeField()
    document_consent_at = models.DateTimeField(null=True, blank=True)
    privacy_policy_version = models.CharField(max_length=24, default="2026-11-01")

    status = models.CharField(
        max_length=20, choices=ServiceStatus.choices, default=ServiceStatus.PENDING
    )
    review_status = models.CharField(
        max_length=16, choices=ReviewStatus.choices, default=ReviewStatus.PENDING
    )
    internal_notes = models.TextField(blank=True)
    quote_amount = models.DecimalField(
        "Quoted fee (KES)",
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0.01)],
        help_text="A quote is not a payment or proof of payment.",
    )
    quote_notes = models.TextField(blank=True)
    quote_sent_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_financial_analysis_requests",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)
    last_contact_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "financial analysis request"
        verbose_name_plural = "financial analysis requests"

    def __str__(self):
        return f"{self.public_reference} — {self.business_name or self.contact_name}"

    @property
    def public_reference(self):
        return str(self.reference).split("-")[0].upper()

    def clean(self):
        super().clean()
        allowed_services = {
            "statement_review",
            "business_plan",
            "cash_flow",
            "budget_forecast",
            "funding_readiness",
            "other",
        }
        if not self.services_requested or not set(self.services_requested).issubset(allowed_services):
            raise ValidationError({"services_requested": "Select at least one valid service."})
        if (
            self.applicant_type == self.ApplicantType.BUSINESS
            and not self.business_name.strip()
        ):
            raise ValidationError({"business_name": "Enter the business or organisation name."})
        if self.preferred_contact == self.ContactPreference.EMAIL and not self.email.strip():
            raise ValidationError({"email": "An email is required for the selected contact method."})
        if (
            self.preferred_contact in {self.ContactPreference.PHONE, self.ContactPreference.WHATSAPP}
            and not self.phone.strip()
        ):
            raise ValidationError({"phone": "A phone number is required for the selected contact method."})
        if self.request_type == self.RequestType.BUSINESS_READINESS:
            if not self.business_goal.strip():
                raise ValidationError({"business_goal": "Describe the business goal for this pilot."})
            if not self.current_challenge.strip():
                raise ValidationError({"current_challenge": "Describe the main business challenge."})
            if (self.average_monthly_sales is None) != (self.average_monthly_costs is None):
                raise ValidationError(
                    "Enter both monthly sales and monthly costs, or leave both blank."
                )
        if self.status in {self.ServiceStatus.QUOTED, self.ServiceStatus.ACCEPTED}:
            if self.quote_amount is None:
                raise ValidationError(
                    {"quote_amount": "Record the fee before marking a request as quoted."}
                )
        if self.status in {
            self.ServiceStatus.ACCEPTED,
            self.ServiceStatus.IN_PROGRESS,
            self.ServiceStatus.COMPLETED,
        } and self.quote_amount is None:
            raise ValidationError({"quote_amount": "A recorded quote is required for this status."})


class FinancialAnalysisDocument(models.Model):
    class DocumentType(models.TextChoices):
        FINANCIAL_STATEMENT = "statement", "Financial statement or accounts"
        BUSINESS_PLAN = "business_plan", "Business plan"
        CASH_FLOW = "cash_flow", "Cash-flow or budget records"
        SALES_RECORDS = "sales_records", "Sales or bookkeeping records"
        OTHER = "other", "Other relevant document"

    class ReviewStatus(models.TextChoices):
        PENDING = "pending", "Pending review"
        REVIEWED = "reviewed", "Reviewed"
        FOLLOW_UP = "follow_up", "Follow-up required"
        NOT_ACCEPTED = "not_accepted", "Not accepted"

    reference = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    request = models.ForeignKey(
        FinancialAnalysisRequest, on_delete=models.CASCADE, related_name="documents"
    )
    document_type = models.CharField(max_length=16, choices=DocumentType.choices)
    description = models.CharField(max_length=200, blank=True)
    file = models.FileField(upload_to=private_financial_analysis_document_path)
    review_status = models.CharField(
        max_length=16, choices=ReviewStatus.choices, default=ReviewStatus.PENDING
    )
    review_notes = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_financial_analysis_documents",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    uploaded_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        ordering = ["uploaded_at"]

    def __str__(self):
        return f"{self.get_document_type_display()} — {self.request}"

    def clean(self):
        super().clean()
        if self.review_status == self.ReviewStatus.REVIEWED and not self.review_notes.strip():
            raise ValidationError(
                {"review_notes": "Record what was reviewed before marking this document reviewed."}
            )


class BusinessReadinessDraft(models.Model):
    class ReviewStatus(models.TextChoices):
        DRAFT = "draft", "Draft — staff review required"
        APPROVED = "approved", "Approved by staff"

    request = models.OneToOneField(
        FinancialAnalysisRequest,
        on_delete=models.CASCADE,
        related_name="readiness_draft",
    )
    generation_method = models.CharField(max_length=32, default="rules-v1")
    business_summary = models.TextField()
    cash_flow = models.JSONField(default=dict)
    key_gaps = models.JSONField(default=list)
    next_steps = models.JSONField(default=list)
    source_citations = models.JSONField(default=list)
    review_status = models.CharField(
        max_length=16,
        choices=ReviewStatus.choices,
        default=ReviewStatus.DRAFT,
    )
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="generated_business_readiness_drafts",
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_business_readiness_drafts",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "business readiness draft"
        verbose_name_plural = "business readiness drafts"

    def __str__(self):
        return f"Readiness draft for {self.request.public_reference}"

    def clean(self):
        super().clean()
        if (
            self.review_status == self.ReviewStatus.APPROVED
            and not self.review_notes.strip()
        ):
            raise ValidationError(
                {"review_notes": "Add reviewer notes before approving this draft."}
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


def private_risk_assessment_document_path(instance, filename):
    suffix = filename.rsplit(".", 1)[-1].lower() if "." in filename else "bin"
    return f"risk-assessments/{instance.request.reference}/{uuid.uuid4()}.{suffix}"


class RiskAssessmentRequest(models.Model):
    class ApplicantType(models.TextChoices):
        INDIVIDUAL = "individual", "Individual or sole proprietor"
        BUSINESS = "business", "Business, group, or organisation"

    class ContactPreference(models.TextChoices):
        PHONE = "phone", "Phone or SMS"
        WHATSAPP = "whatsapp", "WhatsApp"
        EMAIL = "email", "Email"

    class EnterpriseStage(models.TextChoices):
        PRODUCTION = "production", "Production or farming"
        AGGREGATION = "aggregation", "Aggregation or cooperatives"
        PROCESSING = "processing", "Processing or value addition"
        DISTRIBUTION = "distribution", "Wholesale or distribution"
        RETAIL = "retail", "Retail or direct sales"
        SERVICES = "services", "Agricultural services or inputs"
        MULTIPLE = "multiple", "Multiple stages"
        OTHER = "other", "Other or not sure"

    class TimeHorizon(models.TextChoices):
        IMMEDIATE = "immediate", "Immediate decision (within 3 months)"
        THIS_YEAR = "this_year", "Within 12 months"
        LONGER_TERM = "longer_term", "More than 12 months"
        EXPLORATORY = "exploratory", "Exploratory; no fixed deadline"

    class ServiceStatus(models.TextChoices):
        PENDING = "pending", "New request"
        IN_REVIEW = "in_review", "Under initial review"
        NEEDS_INFORMATION = "needs_information", "More information requested"
        QUOTED = "quoted", "Quote sent"
        ACCEPTED = "accepted", "Quote accepted"
        IN_PROGRESS = "in_progress", "Assessment in progress"
        COMPLETED = "completed", "Completed"
        DECLINED = "declined", "Not proceeding"
        CANCELLED = "cancelled", "Cancelled"

    reference = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    applicant_type = models.CharField(max_length=16, choices=ApplicantType.choices)
    contact_name = models.CharField(max_length=160)
    business_name = models.CharField(max_length=180, blank=True)
    phone = models.CharField(max_length=32, blank=True)
    email = models.EmailField(blank=True)
    preferred_contact = models.CharField(max_length=12, choices=ContactPreference.choices)
    county = models.CharField(max_length=32, choices=[(county, county) for county in COUNTIES])
    sector = models.CharField(max_length=120, blank=True)
    enterprise_stage = models.CharField(
        max_length=16, choices=EnterpriseStage.choices, blank=True
    )
    assessment_areas = models.JSONField(default=list)
    risk_priorities = models.JSONField(default=list)
    opportunity_priorities = models.JSONField(default=list)
    time_horizon = models.CharField(max_length=16, choices=TimeHorizon.choices)
    request_summary = models.TextField()
    contact_consent_at = models.DateTimeField()
    document_consent_at = models.DateTimeField(null=True, blank=True)
    privacy_policy_version = models.CharField(max_length=24, default="2026-11-01")
    status = models.CharField(
        max_length=20, choices=ServiceStatus.choices, default=ServiceStatus.PENDING
    )
    internal_notes = models.TextField(blank=True)
    quote_amount = models.DecimalField(
        "Quoted fee (KES)",
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0.01)],
        help_text="A quote is not a payment or proof of payment.",
    )
    quote_notes = models.TextField(blank=True)
    quote_sent_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_risk_assessment_requests",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)
    last_contact_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "risk and opportunity assessment request"
        verbose_name_plural = "risk and opportunity assessment requests"

    def __str__(self):
        return f"{self.public_reference} — {self.business_name or self.contact_name}"

    @property
    def public_reference(self):
        return str(self.reference).split("-")[0].upper()

    def clean(self):
        super().clean()
        allowed_assessment_areas = {
            "enterprise",
            "market",
            "operations",
            "financial_resilience",
            "climate_environment",
            "supply_chain",
            "governance_compliance",
            "technology",
            "other",
        }
        allowed_risk_priorities = {
            "production",
            "climate",
            "market",
            "financial",
            "operations",
            "supply_chain",
            "governance",
            "regulatory",
            "technology",
            "not_sure",
        }
        allowed_opportunity_priorities = {
            "market_growth",
            "value_addition",
            "productivity",
            "climate_resilience",
            "digital",
            "partnerships",
            "finance_readiness",
            "new_products",
            "not_sure",
        }
        for field, selected, allowed in (
            ("assessment_areas", self.assessment_areas, allowed_assessment_areas),
            ("risk_priorities", self.risk_priorities, allowed_risk_priorities),
            ("opportunity_priorities", self.opportunity_priorities, allowed_opportunity_priorities),
        ):
            if not selected or not isinstance(selected, list) or not set(selected).issubset(allowed):
                raise ValidationError({field: "Select at least one valid option."})
        if self.applicant_type == self.ApplicantType.BUSINESS and not self.business_name.strip():
            raise ValidationError({"business_name": "Enter the business or organisation name."})
        if self.preferred_contact == self.ContactPreference.EMAIL and not self.email.strip():
            raise ValidationError({"email": "An email is required for the selected contact method."})
        if self.preferred_contact in {
            self.ContactPreference.PHONE,
            self.ContactPreference.WHATSAPP,
        } and not self.phone.strip():
            raise ValidationError({"phone": "A phone number is required for the selected contact method."})
        if self.status in {self.ServiceStatus.QUOTED, self.ServiceStatus.ACCEPTED}:
            if self.quote_amount is None:
                raise ValidationError(
                    {"quote_amount": "Record the fee before marking a request as quoted."}
                )
        if self.status in {
            self.ServiceStatus.ACCEPTED,
            self.ServiceStatus.IN_PROGRESS,
            self.ServiceStatus.COMPLETED,
        } and self.quote_amount is None:
            raise ValidationError({"quote_amount": "A recorded quote is required for this status."})


class RiskAssessmentDocument(models.Model):
    class DocumentType(models.TextChoices):
        BUSINESS_PROFILE = "business_profile", "Business or enterprise profile"
        PRODUCTION = "production", "Production or operations summary"
        MARKET = "market", "Market or customer summary"
        FINANCIAL = "financial", "Redacted financial summary"
        OTHER = "other", "Other relevant document"

    class ReviewStatus(models.TextChoices):
        PENDING = "pending", "Pending review"
        REVIEWED = "reviewed", "Reviewed"
        FOLLOW_UP = "follow_up", "Follow-up required"
        NOT_ACCEPTED = "not_accepted", "Not accepted"

    reference = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    request = models.ForeignKey(
        RiskAssessmentRequest, on_delete=models.CASCADE, related_name="documents"
    )
    document_type = models.CharField(max_length=24, choices=DocumentType.choices)
    description = models.CharField(max_length=200, blank=True)
    file = models.FileField(upload_to=private_risk_assessment_document_path)
    review_status = models.CharField(
        max_length=16, choices=ReviewStatus.choices, default=ReviewStatus.PENDING
    )
    review_notes = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_risk_assessment_documents",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    uploaded_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        ordering = ["uploaded_at"]

    def __str__(self):
        return f"{self.get_document_type_display()} — {self.request}"

    def clean(self):
        super().clean()
        if self.review_status == self.ReviewStatus.REVIEWED and not self.review_notes.strip():
            raise ValidationError(
                {"review_notes": "Record what was reviewed before marking this document reviewed."}
            )


class ResearcherApplication(models.Model):
    class ApplicantType(models.TextChoices):
        ORGANISATION = "organisation", "Research organisation"
        UNIVERSITY = "university", "University or academic institution"
        MARKETING = "marketing", "Marketing or insights company"
        STUDENT = "student", "Research student"

    class ReviewStatus(models.TextChoices):
        PENDING = "pending", "Pending vetting"
        IN_REVIEW = "in_review", "Under review"
        NEEDS_INFORMATION = "needs_information", "More information requested"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Not approved"
        SUSPENDED = "suspended", "Access suspended"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="researcher_application",
    )
    applicant_type = models.CharField(max_length=16, choices=ApplicantType.choices)
    organisation_name = models.CharField(max_length=200)
    role_title = models.CharField(max_length=120, blank=True)
    phone = models.CharField(max_length=32)
    website = models.URLField(blank=True)
    country = models.CharField(max_length=100, default="Kenya")
    supervisor_name = models.CharField(max_length=160, blank=True)
    supervisor_email = models.EmailField(blank=True)
    research_purpose = models.TextField()
    methods_summary = models.TextField()
    privacy_policy_url = models.URLField(blank=True)
    data_protection_contact = models.CharField(max_length=200, blank=True)
    review_status = models.CharField(
        max_length=24, choices=ReviewStatus.choices, default=ReviewStatus.PENDING
    )
    review_notes = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="vetted_researcher_applications",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    consent_at = models.DateTimeField()
    last_contact_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Portal E researcher application"
        verbose_name_plural = "Portal E researcher applications"

    def __str__(self):
        return f"{self.organisation_name} — {self.user.email}"

    def clean(self):
        super().clean()
        if self.applicant_type == self.ApplicantType.STUDENT:
            if not self.supervisor_name.strip() or not self.supervisor_email.strip():
                raise ValidationError(
                    {
                        "supervisor_name": "A student application requires an academic or project supervisor.",
                        "supervisor_email": "Provide the supervisor's institutional email.",
                    }
                )


class ResearchStudy(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        SUBMITTED = "submitted", "Submitted for review"
        NEEDS_CHANGES = "needs_changes", "Changes requested"
        QUOTE_SENT = "quote_sent", "Fee quote sent"
        QUOTE_ACCEPTED = "quote_accepted", "Fee quote accepted"
        APPROVED = "approved", "Approved for deployment"
        PUBLISHED = "published", "Open for invited respondents"
        PAUSED = "paused", "Paused"
        CLOSED = "closed", "Closed"
        DECLINED = "declined", "Not approved"

    class EthicsStatus(models.TextChoices):
        APPROVED = "approved", "Ethics approval obtained"
        PENDING = "pending", "Ethics approval pending"
        NOT_REQUIRED = "not_required", "Formal ethics review not required"

    class Audience(models.TextChoices):
        FARMER_INDIVIDUAL = "farmer_individual", "Individual farmer contacts"
        FARMER_GROUP = "farmer_group", "Farmer-group contacts"
        SUPPLIER = "supplier", "Input or service suppliers"
        BUYER = "buyer", "Produce buyers"
        SERVICE_PROVIDER = "service_provider", "Professional service providers"

    researcher = models.ForeignKey(
        ResearcherApplication, on_delete=models.PROTECT, related_name="studies"
    )
    title = models.CharField(max_length=200)
    purpose = models.TextField()
    intended_use = models.TextField()
    methodology = models.TextField()
    target_audiences = models.JSONField(default=list)
    target_counties = models.JSONField(default=list, blank=True)
    target_sample_size = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(5), MaxValueValidator(5000)]
    )
    ethics_status = models.CharField(max_length=16, choices=EthicsStatus.choices)
    ethics_body = models.CharField(max_length=200, blank=True)
    ethics_reference = models.CharField(max_length=120, blank=True)
    respondent_consent_text = models.TextField(max_length=1000)
    closes_at = models.DateTimeField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    fee_quote_kes = models.DecimalField(
        "Quoted fee (KES)",
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0.01)],
    )
    fee_quote_notes = models.TextField(blank=True)
    fee_quote_sent_at = models.DateTimeField(null=True, blank=True)
    fee_accepted_at = models.DateTimeField(null=True, blank=True)
    staff_notes = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_research_studies",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def clean(self):
        super().clean()
        valid_audiences = {value for value, _ in self.Audience.choices}
        if not self.target_audiences or not set(self.target_audiences).issubset(valid_audiences):
            raise ValidationError({"target_audiences": "Select at least one valid audience."})
        valid_counties = set(COUNTIES)
        if not set(self.target_counties).issubset(valid_counties):
            raise ValidationError({"target_counties": "Select only valid counties."})
        if self.status in {
            self.Status.QUOTE_SENT,
            self.Status.QUOTE_ACCEPTED,
            self.Status.APPROVED,
            self.Status.PUBLISHED,
        } and self.fee_quote_kes is None:
            raise ValidationError({"fee_quote_kes": "A fee quote is required for this status."})
        if self.status in {
            self.Status.QUOTE_ACCEPTED,
            self.Status.APPROVED,
            self.Status.PUBLISHED,
        } and not self.fee_accepted_at:
            raise ValidationError({"fee_accepted_at": "The researcher must accept the fee quote first."})
        if self.status in {self.Status.PUBLISHED, self.Status.APPROVED}:
            if self.ethics_status == self.EthicsStatus.PENDING:
                raise ValidationError({"ethics_status": "Ethics review must be resolved before approval."})
            if self.ethics_status == self.EthicsStatus.APPROVED and not self.ethics_body.strip():
                raise ValidationError({"ethics_body": "Record the ethics approval body."})
            if not self.questions.exists():
                raise ValidationError({"status": "Add at least one approved question before approval."})
        if self.status == self.Status.PUBLISHED and self.responses.count() >= self.target_sample_size:
            raise ValidationError({"status": "The planned response target has already been reached."})
        if self.status == self.Status.PUBLISHED and self.closes_at <= timezone.now():
            raise ValidationError({"closes_at": "The questionnaire closing time must be in the future."})


class ResearchQuestion(models.Model):
    class AnswerType(models.TextChoices):
        SINGLE = "single", "Choose one answer"
        MULTIPLE = "multiple", "Choose all that apply"

    study = models.ForeignKey(ResearchStudy, on_delete=models.CASCADE, related_name="questions")
    position = models.PositiveSmallIntegerField()
    prompt = models.CharField(max_length=240)
    answer_type = models.CharField(max_length=12, choices=AnswerType.choices)
    options = models.JSONField(default=list)
    required = models.BooleanField(default=True)

    class Meta:
        ordering = ["position"]
        constraints = [
            models.UniqueConstraint(fields=["study", "position"], name="unique_study_question_position")
        ]

    def __str__(self):
        return f"{self.position}. {self.prompt}"

    def clean(self):
        super().clean()
        if not isinstance(self.options, list) or not 2 <= len(self.options) <= 8:
            raise ValidationError({"options": "Each question must have between 2 and 8 answer options."})
        if any(not isinstance(option, str) or not option.strip() for option in self.options):
            raise ValidationError({"options": "Answer options must be non-empty text."})
        normalized = [option.strip().casefold() for option in self.options]
        if len(normalized) != len(set(normalized)):
            raise ValidationError({"options": "Answer options must be unique."})


def research_invitation_expiry():
    return timezone.now() + timedelta(days=14)


class ResearchInvitation(models.Model):
    study = models.ForeignKey(ResearchStudy, on_delete=models.CASCADE, related_name="invitations")
    farmer_profile = models.ForeignKey(
        FarmerProfile, on_delete=models.CASCADE, null=True, blank=True, related_name="research_invitations"
    )
    partner_profile = models.ForeignKey(
        PartnerProfile, on_delete=models.CASCADE, null=True, blank=True, related_name="research_invitations"
    )
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    invited_at = models.DateTimeField(default=timezone.now, editable=False)
    expires_at = models.DateTimeField(default=research_invitation_expiry)
    completed_on = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-invited_at"]
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(
                        farmer_profile__isnull=False,
                        partner_profile__isnull=True,
                        completed_on__isnull=True,
                    )
                    | models.Q(
                        farmer_profile__isnull=True,
                        partner_profile__isnull=False,
                        completed_on__isnull=True,
                    )
                    | models.Q(
                        farmer_profile__isnull=True,
                        partner_profile__isnull=True,
                        completed_on__isnull=False,
                    )
                ),
                name="research_invitation_has_one_member",
            ),
            models.UniqueConstraint(
                fields=["study", "farmer_profile"],
                condition=models.Q(farmer_profile__isnull=False),
                name="unique_study_farmer_invitation",
            ),
            models.UniqueConstraint(
                fields=["study", "partner_profile"],
                condition=models.Q(partner_profile__isnull=False),
                name="unique_study_partner_invitation",
            ),
        ]

    def __str__(self):
        return f"Invitation for {self.study}"

    def clean(self):
        super().clean()
        if self.completed_on:
            if self.farmer_profile_id or self.partner_profile_id:
                raise ValidationError("Completed invitations must not retain member identity links.")
            return
        if bool(self.farmer_profile_id) == bool(self.partner_profile_id):
            raise ValidationError("Select exactly one opted-in farmer or partner profile.")
        if self.farmer_profile_id and not self.farmer_profile.research_invite_consent_at:
            raise ValidationError({"farmer_profile": "This farmer has not opted in to research invitations."})
        if self.partner_profile_id and not self.partner_profile.research_invite_consent_at:
            raise ValidationError({"partner_profile": "This partner has not opted in to research invitations."})
        if self.study_id and self.study.status != ResearchStudy.Status.PUBLISHED:
            raise ValidationError({"study": "Invitations can only be created for an approved study."})
        if self.study_id and self.study.responses.count() >= self.study.target_sample_size:
            raise ValidationError({"study": "The planned response target has already been reached."})
        if self.study_id and self.farmer_profile_id:
            audience = (
                ResearchStudy.Audience.FARMER_GROUP
                if self.farmer_profile.registration_type == FarmerProfile.RegistrationType.GROUP
                else ResearchStudy.Audience.FARMER_INDIVIDUAL
            )
            if audience not in self.study.target_audiences:
                raise ValidationError({"farmer_profile": "This study does not target this farmer category."})
            if (
                self.study.target_counties
                and self.farmer_profile.county not in self.study.target_counties
            ):
                raise ValidationError({"farmer_profile": "This study does not target this county."})
        if self.study_id and self.partner_profile_id:
            role_audiences = {
                "supplier": ResearchStudy.Audience.SUPPLIER,
                "buyer": ResearchStudy.Audience.BUYER,
                "service_provider": ResearchStudy.Audience.SERVICE_PROVIDER,
            }
            if not set(self.partner_profile.roles).intersection(
                role for role, audience in role_audiences.items()
                if audience in self.study.target_audiences
            ):
                raise ValidationError({"partner_profile": "This study does not target this partner category."})
            if (
                self.study.target_counties
                and self.partner_profile.county not in self.study.target_counties
            ):
                raise ValidationError({"partner_profile": "This study does not target this county."})

class ResearchResponse(models.Model):
    study = models.ForeignKey(ResearchStudy, on_delete=models.CASCADE, related_name="responses")
    answers = models.JSONField()
    consented_on = models.DateField(default=timezone.localdate, editable=False)
    submitted_on = models.DateField(default=timezone.localdate, editable=False)

    class Meta:
        ordering = ["submitted_on"]

    def __str__(self):
        return f"Anonymous response for {self.study}"


class ServicePlan(models.Model):
    slug = models.SlugField(max_length=48, unique=True)
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    tagline = models.CharField(max_length=220)
    description = models.TextField()
    features = models.JSONField(default=list, blank=True)
    active = models.BooleanField(default=True)
    display_order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["display_order", "price"]

    def __str__(self):
        return f"{self.name} — KSh {self.price:,.0f}"

    def clean(self):
        super().clean()
        if self.price <= 0 or self.price != self.price.to_integral_value():
            raise ValidationError(
                {"price": "M-PESA package prices must be a positive whole number of Kenyan shillings."}
            )


class BetaInvite(models.Model):
    farmer_profile = models.ForeignKey(
        FarmerProfile,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="beta_invites",
    )
    partner_profile = models.ForeignKey(
        PartnerProfile,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="beta_invites",
    )
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_beta_invites",
    )
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    expires_at = models.DateTimeField(default=default_beta_invite_expiry)
    active = models.BooleanField(default=True)
    redeemed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Private beta invite {self.token}"

    @property
    def profile_is_verified(self):
        if self.farmer_profile_id:
            return self.farmer_profile.verification_status == FarmerProfile.VerificationStatus.VERIFIED
        if self.partner_profile_id:
            return self.partner_profile.verification_status == PartnerProfile.ReviewStatus.VERIFIED
        return False

    def clean(self):
        super().clean()
        if bool(self.farmer_profile_id) == bool(self.partner_profile_id):
            raise ValidationError("Select exactly one verified farmer or entrepreneur profile.")
        if self.active and self.farmer_profile_id and not self.profile_is_verified:
            raise ValidationError({"farmer_profile": "Only MoFirms-verified farmers can be invited."})
        if self.active and self.partner_profile_id and not self.profile_is_verified:
            raise ValidationError(
                {"partner_profile": "Only MoFirms-verified entrepreneurs can be invited."}
            )
class BetaEnrollment(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Awaiting beta approval"
        APPROVED = "approved", "Approved for private beta"
        DECLINED = "declined", "Not approved"
        CLOSED = "closed", "Access closed"

    invite = models.OneToOneField(
        BetaInvite, on_delete=models.CASCADE, related_name="enrollment"
    )
    access_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    consent_at = models.DateTimeField()
    terms_version = models.CharField(max_length=24, default="beta-2026-11-07")
    review_notes = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_beta_enrollments",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.profile_label} — {self.get_status_display()}"

    @property
    def profile(self):
        return self.invite.farmer_profile or self.invite.partner_profile

    @property
    def profile_label(self):
        profile = self.profile
        if isinstance(profile, FarmerProfile):
            return profile.group_name or profile.full_name
        return profile.business_name or profile.trading_name or profile.contact_name

    def clean(self):
        super().clean()
        if (
            self.status == self.Status.APPROVED
            and self.invite_id
            and (not self.invite.active or not self.invite.profile_is_verified)
        ):
            raise ValidationError("Private beta access requires a verified MoFirms profile.")


class MpesaPayment(models.Model):
    class Status(models.TextChoices):
        INITIATING = "initiating", "Starting M-PESA request"
        PENDING = "pending", "Awaiting M-PESA payment"
        PAID = "paid", "Paid"
        FAILED = "failed", "Failed"

    enrollment = models.ForeignKey(
        BetaEnrollment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payments",
    )
    plan = models.ForeignKey(ServicePlan, on_delete=models.PROTECT, related_name="payments")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    phone_number = models.CharField(max_length=16)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.INITIATING)
    checkout_request_id = models.CharField(max_length=120, unique=True, null=True, blank=True)
    merchant_request_id = models.CharField(max_length=120, blank=True)
    mpesa_receipt = models.CharField(max_length=32, unique=True, null=True, blank=True)
    result_code = models.CharField(max_length=24, blank=True)
    result_description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["enrollment"],
                condition=Q(status__in=["initiating", "pending"]),
                name="one_active_mpesa_payment_per_beta_enrollment",
            )
        ]

    def __str__(self):
        return f"{self.plan.name} — {self.get_status_display()} — {self.phone_number}"

    def clean(self):
        super().clean()
        if self.amount != self.plan.price:
            raise ValidationError({"amount": "The payment amount must match the selected plan price."})


class ConsultationLead(models.Model):
    class PreferredContact(models.TextChoices):
        EMAIL = "email", "Email"
        PHONE = "phone", "Phone"
        WHATSAPP = "whatsapp", "WhatsApp"

    class Category(models.TextChoices):
        AGRIBUSINESS = "agribusiness", "Agribusiness advice"
        BUSINESS_INTELLIGENCE = "business_intelligence", "Business intelligence"
        TRAINING = "training", "Training"
        PRODUCTS = "products", "Products"
        PROJECT = "project", "Project collaboration"
        SMART_HASIBU = "smart_hasibu", "SmartHasibu waitlist"
        OTHER = "other", "Other"

    class Status(models.TextChoices):
        NEW = "new", "New"
        REVIEWING = "reviewing", "Under review"
        CONTACTED = "contacted", "Contacted"
        QUALIFIED = "qualified", "Qualified opportunity"
        CLOSED = "closed", "Closed"
        SPAM = "spam", "Spam"

    reference = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    full_name = models.CharField(max_length=160)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=32, blank=True)
    preferred_contact = models.CharField(max_length=12, choices=PreferredContact.choices)
    organisation_or_county = models.CharField(max_length=180, blank=True)
    category = models.CharField(max_length=32, choices=Category.choices)
    message = models.CharField(max_length=1200)
    privacy_consent_at = models.DateTimeField()
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.NEW)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_consultation_leads",
    )
    internal_notes = models.TextField(blank=True)
    last_contact_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "consultation lead"
        verbose_name_plural = "consultation leads"

    def __str__(self):
        return f"{self.public_reference} — {self.full_name}"

    @property
    def public_reference(self):
        return str(self.reference).split("-")[0].upper()

    def clean(self):
        super().clean()
        if self.preferred_contact == self.PreferredContact.EMAIL and not self.email.strip():
            raise ValidationError({"email": "An email is required for the selected contact method."})
        if self.preferred_contact in {
            self.PreferredContact.PHONE,
            self.PreferredContact.WHATSAPP,
        } and not self.phone.strip():
            raise ValidationError({"phone": "A phone number is required for the selected contact method."})


class NewsletterSubscription(models.Model):
    class Topic(models.TextChoices):
        FARMING = "farming", "Farming and agribusiness"
        ENTREPRENEURSHIP = "entrepreneurship", "Entrepreneurship and business advisory"
        RISK_ASSESSMENT = "risk_assessment", "Business risk assessment"

    class Status(models.TextChoices):
        ACTIVE = "active", "Subscribed"
        UNSUBSCRIBED = "unsubscribed", "Unsubscribed"

    email = models.EmailField(unique=True)
    topics = models.JSONField(default=list)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE)
    consent_at = models.DateTimeField()
    privacy_policy_version = models.CharField(max_length=24, default="2026-11-01")
    unsubscribe_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    unsubscribed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        self.email = self.email.strip().lower()
        super().save(*args, **kwargs)
