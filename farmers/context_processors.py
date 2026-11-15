from django.conf import settings


def portal_settings(request):
    return {
        "mofirms_contact_email": settings.MOFIRMS_CONTACT_EMAIL,
        "portal_is_production": (
            settings.DJANGO_ENVIRONMENT == "production"
            and not settings.DEBUG
            and not settings.DEMO_MODE
        ),
    }
