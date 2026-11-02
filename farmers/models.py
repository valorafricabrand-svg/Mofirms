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
    applicant_type = models.CharField(max_length=16, choices=ApplicantType.choices)
    contact_name = models.CharField(max_length=160)
    business_name = models.CharField(max_length=180, blank=True)
    phone = models.CharField(max_length=32, blank=True)
    email = models.EmailField(blank=True)
    preferred_contact = models.CharField(max_length=12, choices=ContactPreference.choices)
    county = models.CharField(max_length=32, choices=[(county, county) for county in COUNTIES])
    sector = models.CharField(max_length=120, blank=True)
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
