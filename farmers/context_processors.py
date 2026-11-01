from django.conf import settings


def portal_settings(request):
    return {"mofirms_contact_email": settings.MOFIRMS_CONTACT_EMAIL}
