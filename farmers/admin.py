from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.html import format_html
from django.urls import reverse

from .models import (
    BusinessReadinessDraft,
    ConsultationLead,
    FarmerDocument,
    FarmerProfile,
    FinancialAnalysisDocument,
    FinancialAnalysisRequest,
    BetaEnrollment,
    BetaInvite,
    MpesaPayment,
    NewsletterSubscription,
    PartnerDocument,
    PartnerProfile,
    RiskAssessmentDocument,
    RiskAssessmentRequest,
    ResearchInvitation,
    ResearchQuestion,
    ResearchStudy,
    ResearcherApplication,
    ServicePlan,
)
from .readiness_drafting import save_readiness_draft


@admin.register(NewsletterSubscription)
class NewsletterSubscriptionAdmin(admin.ModelAdmin):
    list_display = ("email", "status", "topics_display", "consent_at", "created_at")
    list_filter = ("status", "consent_at", "created_at")
    search_fields = ("email",)
    readonly_fields = (
        "unsubscribe_token",
        "consent_at",
        "privacy_policy_version",
        "unsubscribed_at",
        "created_at",
        "updated_at",
    )
    fields = (
        "email",
        "topics",
        "status",
        "unsubscribe_token",
        "consent_at",
        "privacy_policy_version",
        "unsubscribed_at",
        "created_at",
        "updated_at",
    )
    actions = ("unsubscribe_selected",)

    @admin.display(description="Topics")
    def topics_display(self, obj):
        labels = dict(NewsletterSubscription.Topic.choices)
        return ", ".join(labels.get(topic, topic) for topic in obj.topics)

    @admin.action(description="Unsubscribe selected addresses")
    def unsubscribe_selected(self, request, queryset):
        now = timezone.now()
        updated = queryset.filter(
            status=NewsletterSubscription.Status.ACTIVE
        ).update(
            status=NewsletterSubscription.Status.UNSUBSCRIBED,
            unsubscribed_at=now,
            updated_at=now,
        )
        self.message_user(request, f"Unsubscribed {updated} address(es).")


@admin.register(ConsultationLead)
class ConsultationLeadAdmin(admin.ModelAdmin):
    list_display = (
        "public_reference",
        "full_name",
        "category",
        "status",
        "assigned_to",
        "created_at",
    )
    list_filter = ("status", "category", "preferred_contact", "created_at")
    search_fields = (
        "full_name",
        "email",
        "phone",
        "organisation_or_county",
        "reference",
    )
    readonly_fields = (
        "reference",
        "privacy_consent_at",
        "created_at",
        "updated_at",
    )
    list_select_related = ("assigned_to",)
    date_hierarchy = "created_at"
    actions = ("mark_contacted_today",)
    fieldsets = (
        (
            "Lead follow-up",
            {"fields": ("reference", "status", "assigned_to", "internal_notes")},
        ),
        (
            "Enquiry and contact",
            {
                "fields": (
                    "full_name",
                    "email",
                    "phone",
                    "preferred_contact",
                    "organisation_or_county",
                    "category",
                    "message",
                )
            },
        ),
        (
            "Consent and retention",
            {
                "fields": (
                    "privacy_consent_at",
                    "last_contact_at",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    @admin.display(description="Reference")
    def public_reference(self, obj):
        return obj.public_reference

    @admin.action(description="Record that contact occurred today")
    def mark_contacted_today(self, request, queryset):
        updated = queryset.update(last_contact_at=timezone.now())
        self.message_user(request, f"Updated the last-contact date for {updated} enquiry/enquiries.")

    def save_model(self, request, obj, form, change):
        if change and "status" in form.changed_data and obj.status == ConsultationLead.Status.CONTACTED:
            obj.last_contact_at = timezone.now()
        super().save_model(request, obj, form, change)


class BetaInviteAdminForm(forms.ModelForm):
    class Meta:
        model = BetaInvite
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "farmer_profile" in self.fields:
            self.fields["farmer_profile"].queryset = FarmerProfile.objects.filter(
                verification_status=FarmerProfile.VerificationStatus.VERIFIED
            )
        if "partner_profile" in self.fields:
            self.fields["partner_profile"].queryset = PartnerProfile.objects.filter(
                verification_status=PartnerProfile.ReviewStatus.VERIFIED
            )


@admin.register(FarmerProfile)
class FarmerProfileAdmin(admin.ModelAdmin):
    list_display = (
        "public_reference",
        "full_name",
        "registration_type",
        "group_name",
        "county",
        "verification_status",
        "identity_review_status",
        "group_review_status",
        "farm_review_status",
        "created_at",
    )


    list_filter = (
        "registration_type",
        "verification_status",
        "identity_review_status",
        "group_review_status",
        "farm_review_status",
        "county",
        "research_invite_consent_at",
        "group_registration_status",
        "created_at",
    )
    search_fields = (
        "full_name",
        "group_name",
        "email",
        "phone",
        "county",
        "group_registration_number",
        "reference",
    )
    readonly_fields = (
        "reference",
        "created_at",
        "updated_at",
        "privacy_consent_at",
        "research_invite_consent_at",
        "document_consent_at",
        "privacy_policy_version",
        "reviewed_by",
        "reviewed_at",
    )
    actions = ("mark_contacted_today",)
    list_select_related = ("reviewed_by",)
    date_hierarchy = "created_at"
    fieldsets = (
        ("Registration and review", {
            "fields": (
                "reference",
                "registration_type",
                "verification_status",
                "identity_review_status",
                "group_review_status",
                "farm_review_status",
                "verification_notes",
                "reviewed_by",
                "reviewed_at",
            )
        }),
        ("Primary contact", {
            "fields": (
                "full_name",
                "phone",
                "email",
                "preferred_contact",
                "preferred_language",
            )
        }),
        ("Group or association", {
            "fields": (
                "group_name",
                "group_type",
                "group_registration_status",
                "group_registration_number",
                "group_member_count",
                "representative_role",
                "group_authorization_confirmed",
            )
        }),
        ("Farm location and profile", {
            "fields": (
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
            )
        }),
        ("Business assessment", {
            "fields": (
                "sales_band",
                "operating_cost_band",
                "finance_need_band",
                "record_keeping",
                "sales_channels",
                "challenges",
                "support_interests",
                "goals",
                "additional_notes",
            )
        }),
        ("Consent, retention, and contact history", {
            "fields": (
                "privacy_consent_at",
                "research_invite_consent_at",
                "document_consent_at",
                "privacy_policy_version",
                "last_contact_at",
                "created_at",
                "updated_at",
            )
        }),
    )

    @admin.display(description="Reference")
    def public_reference(self, obj):
        return obj.public_reference

    @admin.action(description="Record that contact occurred today (retention clock)")
    def mark_contacted_today(self, request, queryset):
        updated = queryset.update(last_contact_at=timezone.now())
        self.message_user(request, f"Updated the last-contact date for {updated} registration(s).")

    def save_model(self, request, obj, form, change):
        review_fields = {
            "verification_status",
            "identity_review_status",
            "group_review_status",
            "farm_review_status",
        }
        if change and review_fields.intersection(form.changed_data):
            obj.reviewed_by = request.user
            obj.reviewed_at = timezone.now()
        super().save_model(request, obj, form, change)


@admin.register(FarmerDocument)
class FarmerDocumentAdmin(admin.ModelAdmin):
    list_display = (
        "reference",
        "profile",
        "document_type",
        "review_status",
        "uploaded_at",
        "secure_download",
    )
    list_filter = ("document_type", "review_status", "uploaded_at")
    search_fields = (
        "profile__full_name",
        "profile__group_name",
        "profile__reference",
        "reference",
    )
    readonly_fields = (
        "reference", "uploaded_at", "secure_download", "reviewed_by", "reviewed_at"
    )
    fields = (
        "reference",
        "profile",
        "document_type",
        "description",
        "secure_download",
        "review_status",
        "review_notes",
        "reviewed_by",
        "reviewed_at",
        "uploaded_at",
    )

    @admin.display(description="Private evidence file")
    def secure_download(self, obj):
        if not obj.pk or not obj.file:
            return "No file"
        url = reverse("download_document", args=[obj.pk])
        return format_html('<a href="{}">Download evidence</a>', url)

    def save_model(self, request, obj, form, change):
        if change and "review_status" in form.changed_data:
            obj.reviewed_by = request.user
            obj.reviewed_at = timezone.now()
        super().save_model(request, obj, form, change)


@admin.register(PartnerProfile)
class PartnerProfileAdmin(admin.ModelAdmin):
    list_display = (
        "public_reference",
        "business_name",
        "contact_name",
        "county",
        "roles_summary",
        "verification_status",
        "business_review_status",
        "offering_review_status",
        "created_at",
    )
    list_filter = (
        "applicant_type",
        "verification_status",
        "identity_review_status",
        "business_review_status",
        "offering_review_status",
        "registration_status",
        "county",
        "research_invite_consent_at",
        "created_at",
    )
    search_fields = (
        "business_name",
        "trading_name",
        "contact_name",
        "email",
        "phone",
        "registration_number",
        "county",
        "reference",
    )
    readonly_fields = (
        "reference",
        "created_at",
        "updated_at",
        "contact_consent_at",
        "listing_referral_consent_at",
        "research_invite_consent_at",
        "document_consent_at",
        "privacy_policy_version",
        "reviewed_by",
        "reviewed_at",
    )
    actions = ("mark_contacted_today",)
    date_hierarchy = "created_at"
    fieldsets = (
        ("Registration and manual review", {
            "fields": (
                "reference",
                "applicant_type",
                "roles",
                "verification_status",
                "identity_review_status",
                "business_review_status",
                "offering_review_status",
                "verification_notes",
                "reviewed_by",
                "reviewed_at",
            )
        }),
        ("Business and primary contact", {
            "fields": (
                "business_name",
                "trading_name",
                "contact_name",
                "phone",
                "email",
                "website",
                "preferred_contact",
                "preferred_language",
                "business_description",
            )
        }),
        ("Organisation details", {
            "fields": (
                "registration_status",
                "registration_number",
                "year_established",
                "years_experience",
                "business_size",
                "staff_band",
            )
        }),
        ("Location and coverage", {
            "fields": (
                "county",
                "sub_county",
                "ward",
                "operating_counties",
                "delivery_methods",
            )
        }),
        ("Supplier profile", {
            "fields": (
                "offer_categories",
                "offer_details",
                "service_description",
                "brands_or_products",
                "service_area",
                "lead_time",
                "minimum_order",
                "prices_and_terms",
            )
        }),
        ("Buyer profile", {
            "fields": (
                "produce_categories",
                "produce_details",
                "sourcing_counties",
                "buyer_capacity",
                "buying_frequency",
                "quality_requirements",
                "payment_terms",
            )
        }),
        ("Service provider profile", {
            "fields": (
                "clients_and_references",
                "licences_and_standards",
                "service_capacity",
                "staff_qualifications",
                "engagement_interests",
            )
        }),
        ("Business needs", {
            "fields": ("challenges", "partnership_goals", "additional_notes")
        }),
        ("Consent and retention", {
            "fields": (
                "contact_consent_at",
                "listing_referral_consent_at",
                "research_invite_consent_at",
                "document_consent_at",
                "privacy_policy_version",
                "last_contact_at",
                "created_at",
                "updated_at",
            )
        }),
    )

    @admin.display(description="Reference")
    def public_reference(self, obj):
        return obj.public_reference

    @admin.display(description="Partner roles")
    def roles_summary(self, obj):
        role_labels = {
            "supplier": "Supplier",
            "buyer": "Produce buyer",
            "service_provider": "Service provider",
        }
        return ", ".join(role_labels.get(role, role) for role in obj.roles)

    @admin.action(description="Record that contact occurred today (retention clock)")
    def mark_contacted_today(self, request, queryset):
        updated = queryset.update(last_contact_at=timezone.now())
        self.message_user(request, f"Updated the last-contact date for {updated} partner(s).")

    def save_model(self, request, obj, form, change):
        review_fields = {
            "verification_status",
            "identity_review_status",
            "business_review_status",
            "offering_review_status",
        }
        if change and review_fields.intersection(form.changed_data):
            obj.reviewed_by = request.user
            obj.reviewed_at = timezone.now()
        super().save_model(request, obj, form, change)


@admin.register(PartnerDocument)
class PartnerDocumentAdmin(admin.ModelAdmin):
    list_display = (
        "reference",
        "profile",
        "document_type",
        "review_status",
        "uploaded_at",
        "secure_download",
    )
    list_filter = ("document_type", "review_status", "uploaded_at")
    search_fields = (
        "profile__business_name",
        "profile__trading_name",
        "profile__contact_name",
        "profile__reference",
        "reference",
    )
    readonly_fields = (
        "reference",
        "uploaded_at",
        "secure_download",
        "reviewed_by",
        "reviewed_at",
    )
    fields = (
        "reference",
        "profile",
        "document_type",
        "description",
        "secure_download",
        "review_status",
        "review_notes",
        "reviewed_by",
        "reviewed_at",
        "uploaded_at",
    )

    @admin.display(description="Private evidence file")
    def secure_download(self, obj):
        if not obj.pk or not obj.file:
            return "No file"
        url = reverse("download_partner_document", args=[obj.pk])
        return format_html('<a href="{}">Download evidence</a>', url)

    def save_model(self, request, obj, form, change):
        if change and "review_status" in form.changed_data:
            obj.reviewed_by = request.user
            obj.reviewed_at = timezone.now()
        super().save_model(request, obj, form, change)


class BusinessReadinessDraftInline(admin.StackedInline):
    model = BusinessReadinessDraft
    extra = 0
    can_delete = False
    fields = (
        "generation_method",
        "business_summary",
        "cash_flow",
        "key_gaps",
        "next_steps",
        "source_citations",
        "review_status",
        "review_notes",
        "generated_by",
        "reviewed_by",
        "reviewed_at",
        "created_at",
        "updated_at",
    )
    readonly_fields = (
        "generation_method",
        "source_citations",
        "generated_by",
        "reviewed_by",
        "reviewed_at",
        "created_at",
        "updated_at",
    )

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(FinancialAnalysisRequest)
class FinancialAnalysisRequestAdmin(admin.ModelAdmin):
    list_display = (
        "public_reference",
        "request_type",
        "contact_name",
        "business_name",
        "services_summary",
        "status",
        "quote_amount",
        "created_at",
    )
    list_filter = (
        "request_type",
        "status",
        "review_status",
        "applicant_type",
        "county",
        "created_at",
    )
    search_fields = ("contact_name", "business_name", "email", "phone", "reference")
    readonly_fields = (
        "reference",
        "contact_consent_at",
        "document_consent_at",
        "privacy_policy_version",
        "reviewed_by",
        "reviewed_at",
        "quote_sent_at",
        "created_at",
        "updated_at",
    )
    actions = ("mark_contacted_today", "generate_readiness_drafts")
    inlines = (BusinessReadinessDraftInline,)
    date_hierarchy = "created_at"
    fieldsets = (
        ("Service request and working status", {
            "fields": (
                "reference",
                "request_type",
                "status",
                "review_status",
                "reviewed_by",
                "reviewed_at",
                "internal_notes",
            )
        }),
        ("Applicant and contact", {
            "fields": (
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
                "seasonality_notes",
            )
        }),
        ("Requested analysis", {
            "fields": (
                "services_requested",
                "financial_period",
                "records_available",
                "accounting_software",
                "annual_revenue_band",
                "funding_need_band",
                "timeline",
                "request_summary",
            )
        }),
        ("Quote", {
            "fields": ("quote_amount", "quote_notes", "quote_sent_at")
        }),
        ("Consent, retention, and contact history", {
            "fields": (
                "contact_consent_at",
                "document_consent_at",
                "privacy_policy_version",
                "last_contact_at",
                "created_at",
                "updated_at",
            )
        }),
    )

    @admin.display(description="Reference")
    def public_reference(self, obj):
        return obj.public_reference

    @admin.display(description="Requested service(s)")
    def services_summary(self, obj):
        labels = dict((
            ("statement_review", "Statements"),
            ("business_plan", "Business plan"),
            ("cash_flow", "Cash flow"),
            ("budget_forecast", "Budget/forecast"),
            ("funding_readiness", "Funding readiness"),
            ("other", "Other"),
        ))
        return ", ".join(labels.get(service, service) for service in obj.services_requested)

    @admin.action(description="Record that contact occurred today (retention clock)")
    def mark_contacted_today(self, request, queryset):
        updated = queryset.update(last_contact_at=timezone.now())
        self.message_user(request, f"Updated the last-contact date for {updated} request(s).")

    @admin.action(description="Generate staff-only readiness drafts")
    def generate_readiness_drafts(self, request, queryset):
        readiness_requests = queryset.filter(
            request_type=FinancialAnalysisRequest.RequestType.BUSINESS_READINESS
        )
        generated = 0
        skipped = queryset.count() - readiness_requests.count()
        for readiness_request in readiness_requests:
            try:
                save_readiness_draft(readiness_request, request.user)
            except ValidationError:
                skipped += 1
            else:
                generated += 1
        self.message_user(
            request,
            f"Generated or refreshed {generated} staff-only draft(s); skipped {skipped} request(s).",
            level="WARNING" if skipped else "INFO",
        )

    def save_model(self, request, obj, form, change):
        review_fields = {"status", "review_status", "quote_amount", "quote_notes"}
        if change and review_fields.intersection(form.changed_data):
            obj.reviewed_by = request.user
            obj.reviewed_at = timezone.now()
        if (
            obj.quote_amount is not None
            and obj.status in {
                FinancialAnalysisRequest.ServiceStatus.QUOTED,
                FinancialAnalysisRequest.ServiceStatus.ACCEPTED,
                FinancialAnalysisRequest.ServiceStatus.IN_PROGRESS,
                FinancialAnalysisRequest.ServiceStatus.COMPLETED,
            }
            and not obj.quote_sent_at
        ):
            obj.quote_sent_at = timezone.now()
        super().save_model(request, obj, form, change)

    def save_formset(self, request, form, formset, change):
        if formset.model is not BusinessReadinessDraft:
            return super().save_formset(request, form, formset, change)

        changed_reviews = set()
        for inline_form in formset.forms:
            if "review_status" in inline_form.changed_data:
                changed_reviews.add(inline_form.instance.pk)
            elif (
                inline_form.initial.get("review_status")
                == BusinessReadinessDraft.ReviewStatus.APPROVED
                and {
                    "business_summary",
                    "cash_flow",
                    "key_gaps",
                    "next_steps",
                    "review_notes",
                }
                .intersection(inline_form.changed_data)
            ):
                inline_form.cleaned_data["review_status"] = (
                    BusinessReadinessDraft.ReviewStatus.DRAFT
                )
                inline_form.cleaned_data["review_notes"] = ""
                changed_reviews.add(inline_form.instance.pk)

        instances = formset.save(commit=False)
        for instance in instances:
            if instance.pk in changed_reviews:
                if instance.review_status == BusinessReadinessDraft.ReviewStatus.APPROVED:
                    instance.reviewed_by = request.user
                    instance.reviewed_at = timezone.now()
                else:
                    instance.reviewed_by = None
                    instance.reviewed_at = None
            instance.save()
        formset.save_m2m()


@admin.register(FinancialAnalysisDocument)
class FinancialAnalysisDocumentAdmin(admin.ModelAdmin):
    list_display = (
        "reference",
        "request",
        "document_type",
        "review_status",
        "uploaded_at",
        "secure_download",
    )
    list_filter = ("document_type", "review_status", "uploaded_at")
    search_fields = (
        "request__contact_name",
        "request__business_name",
        "request__reference",
        "reference",
    )
    readonly_fields = (
        "reference",
        "uploaded_at",
        "secure_download",
        "reviewed_by",
        "reviewed_at",
    )
    fields = (
        "reference",
        "request",
        "document_type",
        "description",
        "secure_download",
        "review_status",
        "review_notes",
        "reviewed_by",
        "reviewed_at",
        "uploaded_at",
    )

    @admin.display(description="Private financial document")
    def secure_download(self, obj):
        if not obj.pk or not obj.file:
            return "No file"
        url = reverse("download_financial_analysis_document", args=[obj.pk])
        return format_html('<a href="{}">Download financial document</a>', url)

    def save_model(self, request, obj, form, change):
        if change and "review_status" in form.changed_data:
            obj.reviewed_by = request.user
            obj.reviewed_at = timezone.now()
        super().save_model(request, obj, form, change)


@admin.register(RiskAssessmentRequest)
class RiskAssessmentRequestAdmin(admin.ModelAdmin):
    list_display = (
        "public_reference",
        "contact_name",
        "business_name",
        "county",
        "status",
        "quote_amount",
        "created_at",
    )
    list_filter = ("status", "applicant_type", "county", "time_horizon", "created_at")
    search_fields = ("contact_name", "business_name", "email", "phone", "reference")
    readonly_fields = (
        "reference",
        "contact_consent_at",
        "document_consent_at",
        "privacy_policy_version",
        "reviewed_by",
        "reviewed_at",
        "quote_sent_at",
        "created_at",
        "updated_at",
    )
    actions = ("mark_contacted_today",)
    date_hierarchy = "created_at"
    fieldsets = (
        ("Assessment request and working status", {
            "fields": (
                "reference",
                "status",
                "reviewed_by",
                "reviewed_at",
                "internal_notes",
            )
        }),
        ("Applicant and contact", {
            "fields": (
                "applicant_type",
                "contact_name",
                "business_name",
                "phone",
                "email",
                "preferred_contact",
                "county",
                "sector",
                "enterprise_stage",
            )
        }),
        ("Assessment scope", {
            "fields": (
                "assessment_areas",
                "risk_priorities",
                "opportunity_priorities",
                "time_horizon",
                "request_summary",
            )
        }),
        ("Specialist fee quote", {
            "fields": ("quote_amount", "quote_notes", "quote_sent_at")
        }),
        ("Consent, retention, and contact history", {
            "fields": (
                "contact_consent_at",
                "document_consent_at",
                "privacy_policy_version",
                "last_contact_at",
                "created_at",
                "updated_at",
            )
        }),
    )

    @admin.display(description="Reference")
    def public_reference(self, obj):
        return obj.public_reference

    @admin.action(description="Record that contact occurred today (retention clock)")
    def mark_contacted_today(self, request, queryset):
        updated = queryset.update(last_contact_at=timezone.now())
        self.message_user(
            request,
            f"Updated the last-contact date for {updated} assessment request(s).",
        )

    def save_model(self, request, obj, form, change):
        review_fields = {"status", "quote_amount", "quote_notes"}
        if change and review_fields.intersection(form.changed_data):
            obj.reviewed_by = request.user
            obj.reviewed_at = timezone.now()
        if (
            obj.quote_amount is not None
            and obj.status in {
                RiskAssessmentRequest.ServiceStatus.QUOTED,
                RiskAssessmentRequest.ServiceStatus.ACCEPTED,
                RiskAssessmentRequest.ServiceStatus.IN_PROGRESS,
                RiskAssessmentRequest.ServiceStatus.COMPLETED,
            }
            and not obj.quote_sent_at
        ):
            obj.quote_sent_at = timezone.now()
        super().save_model(request, obj, form, change)


@admin.register(RiskAssessmentDocument)
class RiskAssessmentDocumentAdmin(admin.ModelAdmin):
    list_display = (
        "reference",
        "request",
        "document_type",
        "review_status",
        "uploaded_at",
        "secure_download",
    )
    list_filter = ("document_type", "review_status", "uploaded_at")
    search_fields = (
        "request__contact_name",
        "request__business_name",
        "request__reference",
        "reference",
    )
    readonly_fields = (
        "reference",
        "uploaded_at",
        "secure_download",
        "reviewed_by",
        "reviewed_at",
    )
    fields = (
        "reference",
        "request",
        "document_type",
        "description",
        "secure_download",
        "review_status",
        "review_notes",
        "reviewed_by",
        "reviewed_at",
        "uploaded_at",
    )

    @admin.display(description="Private assessment file")
    def secure_download(self, obj):
        if not obj.pk or not obj.file:
            return "No file"
        url = reverse("download_risk_assessment_document", args=[obj.pk])
        return format_html('<a href="{}">Download assessment document</a>', url)

    def save_model(self, request, obj, form, change):
        if change and "review_status" in form.changed_data:
            obj.reviewed_by = request.user
            obj.reviewed_at = timezone.now()
        super().save_model(request, obj, form, change)


@admin.register(ResearcherApplication)
class ResearcherApplicationAdmin(admin.ModelAdmin):
    list_display = (
        "organisation_name",
        "user_email",
        "applicant_type",
        "country",
        "review_status",
        "created_at",
    )
    list_filter = ("applicant_type", "review_status", "country", "created_at")
    search_fields = (
        "organisation_name",
        "user__email",
        "phone",
        "supervisor_email",
    )
    readonly_fields = (
        "user",
        "consent_at",
        "last_contact_at",
        "created_at",
        "updated_at",
        "reviewed_by",
        "reviewed_at",
    )
    fieldsets = (
        ("Applicant and vetting", {
            "fields": (
                "user",
                "applicant_type",
                "organisation_name",
                "role_title",
                "country",
                "review_status",
                "review_notes",
                "reviewed_by",
                "reviewed_at",
            )
        }),
        ("Contact and supervisor", {
            "fields": ("phone", "website", "supervisor_name", "supervisor_email")
        }),
        ("Research and data practices", {
            "fields": (
                "research_purpose",
                "methods_summary",
                "privacy_policy_url",
                "data_protection_contact",
            )
        }),
        ("Consent and dates", {
            "fields": ("consent_at", "last_contact_at", "created_at", "updated_at")
        }),
    )
    actions = ("mark_contacted_today",)

    @admin.display(description="Account email")
    def user_email(self, obj):
        return obj.user.email

    @admin.action(description="Record that contact occurred today (retention clock)")
    def mark_contacted_today(self, request, queryset):
        updated = queryset.update(last_contact_at=timezone.now())
        self.message_user(request, f"Updated the last-contact date for {updated} researcher(s).")

    def save_model(self, request, obj, form, change):
        review_changed = change and "review_status" in form.changed_data
        if review_changed:
            obj.reviewed_by = request.user
            obj.reviewed_at = timezone.now()
        super().save_model(request, obj, form, change)
        obj.user.is_active = obj.review_status == ResearcherApplication.ReviewStatus.APPROVED
        obj.user.save(update_fields=["is_active"])

    def has_add_permission(self, request):
        return False


class ResearchQuestionInline(admin.TabularInline):
    model = ResearchQuestion
    extra = 0
    fields = ("position", "prompt", "answer_type", "options", "required")

    def has_add_permission(self, request, obj=None):
        if obj and (obj.status == ResearchStudy.Status.PUBLISHED or obj.responses.exists()):
            return False
        return super().has_add_permission(request, obj)

    def has_change_permission(self, request, obj=None):
        if obj and (obj.status == ResearchStudy.Status.PUBLISHED or obj.responses.exists()):
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj and (obj.status == ResearchStudy.Status.PUBLISHED or obj.responses.exists()):
            return False
        return super().has_delete_permission(request, obj)


class ResearchInvitationInlineForm(forms.ModelForm):
    class Meta:
        model = ResearchInvitation
        fields = ("farmer_profile", "partner_profile")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "farmer_profile" in self.fields:
            self.fields["farmer_profile"].queryset = FarmerProfile.objects.filter(
                research_invite_consent_at__isnull=False
            )
        if "partner_profile" in self.fields:
            self.fields["partner_profile"].queryset = PartnerProfile.objects.filter(
                research_invite_consent_at__isnull=False
            )


class ResearchInvitationInline(admin.TabularInline):
    model = ResearchInvitation
    form = ResearchInvitationInlineForm
    extra = 0
    fields = (
        "farmer_profile",
        "partner_profile",
        "invitation_link",
        "invited_at",
        "expires_at",
        "completed_on",
    )
    readonly_fields = ("invitation_link", "invited_at", "expires_at", "completed_on")
    autocomplete_fields = ("farmer_profile", "partner_profile")

    @admin.display(description="Private invitation link")
    def invitation_link(self, obj):
        if not obj.pk:
            return "Save the invitation to generate its link."
        url = reverse("respond_to_research_invitation", args=[obj.token])
        return format_html('<a href="{}">Open invitation link</a>', url)

    def has_add_permission(self, request, obj=None):
        return bool(
            obj
            and obj.status == ResearchStudy.Status.PUBLISHED
            and obj.closes_at > timezone.now()
            and obj.responses.count() < obj.target_sample_size
            and super().has_add_permission(request, obj)
        )


@admin.register(ResearchStudy)
class ResearchStudyAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "researcher",
        "status",
        "target_sample_size",
        "response_count",
        "closes_at",
        "created_at",
    )
    list_filter = ("status", "ethics_status", "created_at", "closes_at")
    search_fields = ("title", "researcher__organisation_name", "researcher__user__email")
    readonly_fields = (
        "researcher",
        "fee_quote_sent_at",
        "fee_accepted_at",
        "reviewed_by",
        "reviewed_at",
        "created_at",
        "updated_at",
        "closed_at",
        "response_count",
    )
    date_hierarchy = "created_at"
    inlines = (ResearchQuestionInline, ResearchInvitationInline)
    fieldsets = (
        ("Study and review status", {
            "fields": (
                "researcher",
                "title",
                "status",
                "staff_notes",
                "reviewed_by",
                "reviewed_at",
                "response_count",
            )
        }),
        ("Study plan and target audience", {
            "fields": (
                "purpose",
                "intended_use",
                "methodology",
                "target_audiences",
                "target_counties",
                "target_sample_size",
                "closes_at",
            )
        }),
        ("Ethics and respondent information", {
            "fields": (
                "ethics_status",
                "ethics_body",
                "ethics_reference",
                "respondent_consent_text",
            )
        }),
        ("Fee quotation", {
            "fields": (
                "fee_quote_kes",
                "fee_quote_notes",
                "fee_quote_sent_at",
                "fee_accepted_at",
            )
        }),
        ("Dates", {
            "fields": ("created_at", "updated_at", "closed_at")
        }),
    )

    @admin.display(description="Responses")
    def response_count(self, obj):
        return obj.responses.count() if obj.pk else 0

    def save_model(self, request, obj, form, change):
        status_changed = change and "status" in form.changed_data
        if status_changed:
            obj.reviewed_by = request.user
            obj.reviewed_at = timezone.now()
        if obj.status == ResearchStudy.Status.QUOTE_SENT and not obj.fee_quote_sent_at:
            obj.fee_quote_sent_at = timezone.now()
        if obj.status == ResearchStudy.Status.CLOSED and not obj.closed_at:
            obj.closed_at = timezone.now()
        super().save_model(request, obj, form, change)

    def has_add_permission(self, request):
        return False


@admin.register(ResearchInvitation)
class ResearchInvitationAdmin(admin.ModelAdmin):
    list_display = (
        "study",
        "member_summary",
        "invited_at",
        "expires_at",
        "completed_on",
        "invitation_link",
    )
    list_filter = ("study", "invited_at", "expires_at", "completed_on")
    search_fields = (
        "study__title",
        "farmer_profile__full_name",
        "farmer_profile__group_name",
        "partner_profile__business_name",
        "partner_profile__contact_name",
    )
    autocomplete_fields = ("study", "farmer_profile", "partner_profile")
    readonly_fields = ("token", "invited_at", "expires_at", "completed_on", "invitation_link")
    fields = (
        "study",
        "farmer_profile",
        "partner_profile",
        "invitation_link",
        "token",
        "invited_at",
        "expires_at",
        "completed_on",
    )

    @admin.display(description="Invited member (staff only)")
    def member_summary(self, obj):
        return obj.farmer_profile or obj.partner_profile or "Identity removed after response"

    @admin.display(description="Private invitation link")
    def invitation_link(self, obj):
        url = reverse("respond_to_research_invitation", args=[obj.token])
        return format_html('<a href="{}">Open invitation link</a>', url)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if "farmer_profile" in form.base_fields:
            form.base_fields["farmer_profile"].queryset = FarmerProfile.objects.filter(
                research_invite_consent_at__isnull=False
            )
        if "partner_profile" in form.base_fields:
            form.base_fields["partner_profile"].queryset = PartnerProfile.objects.filter(
                research_invite_consent_at__isnull=False
            )
        return form


@admin.register(ServicePlan)
class ServicePlanAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "price", "active", "display_order", "updated_at")
    list_filter = ("active",)
    search_fields = ("name", "slug", "tagline")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("created_at", "updated_at")
    fields = (
        "name",
        "slug",
        "price",
        "tagline",
        "description",
        "features",
        "active",
        "display_order",
        "created_at",
        "updated_at",
    )


@admin.register(BetaInvite)
class BetaInviteAdmin(admin.ModelAdmin):
    form = BetaInviteAdminForm
    list_display = (
        "token",
        "profile_summary",
        "invitation_link",
        "active",
        "expires_at",
        "redeemed_at",
        "created_at",
    )
    list_filter = ("active", "created_at", "expires_at", "redeemed_at")
    search_fields = (
        "farmer_profile__full_name",
        "farmer_profile__group_name",
        "partner_profile__business_name",
        "partner_profile__contact_name",
        "token",
    )
    readonly_fields = ("token", "created_by", "created_at", "redeemed_at", "invitation_link")
    fields = (
        "farmer_profile",
        "partner_profile",
        "token",
        "invitation_link",
        "expires_at",
        "active",
        "created_by",
        "created_at",
        "redeemed_at",
    )

    @admin.display(description="Verified member")
    def profile_summary(self, obj):
        return obj.farmer_profile or obj.partner_profile

    @admin.display(description="Private beta invitation link")
    def invitation_link(self, obj):
        return format_html(
            '<a href="{}">Open private invitation</a>',
            reverse("redeem_beta_invite", args=[obj.token]),
        )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def get_readonly_fields(self, request, obj=None):
        readonly = list(super().get_readonly_fields(request, obj))
        if obj:
            readonly.extend(("farmer_profile", "partner_profile"))
        return tuple(readonly)


@admin.register(BetaEnrollment)
class BetaEnrollmentAdmin(admin.ModelAdmin):
    list_display = (
        "profile_summary",
        "status",
        "reviewed_by",
        "reviewed_at",
        "created_at",
    )
    list_filter = ("status", "created_at", "reviewed_at")
    search_fields = (
        "invite__farmer_profile__full_name",
        "invite__farmer_profile__group_name",
        "invite__partner_profile__business_name",
        "invite__partner_profile__contact_name",
    )
    readonly_fields = (
        "invite",
        "access_token",
        "member_link",
        "consent_at",
        "terms_version",
        "reviewed_by",
        "reviewed_at",
        "created_at",
        "updated_at",
    )
    fields = (
        "invite",
        "access_token",
        "member_link",
        "status",
        "review_notes",
        "consent_at",
        "terms_version",
        "reviewed_by",
        "reviewed_at",
        "created_at",
        "updated_at",
    )

    @admin.display(description="Verified member")
    def profile_summary(self, obj):
        return obj.profile

    @admin.display(description="Private member access link")
    def member_link(self, obj):
        return format_html(
            '<a href="{}">Open private member link</a>',
            reverse("beta_enrollment", args=[obj.access_token]),
        )

    def save_model(self, request, obj, form, change):
        if change and "status" in form.changed_data:
            obj.reviewed_by = request.user
            obj.reviewed_at = timezone.now()
        super().save_model(request, obj, form, change)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(MpesaPayment)
class MpesaPaymentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "enrollment",
        "plan",
        "amount",
        "phone_number",
        "status",
        "mpesa_receipt",
        "created_at",
    )
    list_filter = ("status", "plan", "created_at", "paid_at")
    search_fields = ("phone_number", "mpesa_receipt", "checkout_request_id")
    readonly_fields = tuple(field.name for field in MpesaPayment._meta.fields)
    fields = readonly_fields
    date_hierarchy = "created_at"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            "enrollment", "plan", "enrollment__invite"
        )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
