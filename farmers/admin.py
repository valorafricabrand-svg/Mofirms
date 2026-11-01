from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from django.urls import reverse

from .models import FarmerDocument, FarmerProfile


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
