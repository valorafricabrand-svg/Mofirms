"""Email alerts to MoFirms staff when something needs attention.

Alerts carry no personal details (no names, phone numbers or messages), only what
arrived, its reference and a link into /staff/, because they land in a shared inbox.
"""

import logging
import threading

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse

from .models import (
    ConsultationLead,
    FarmerProfile,
    FinancialAnalysisRequest,
    PartnerProfile,
    ResearcherApplication,
    RiskAssessmentRequest,
    WhatsAppContact,
)

logger = logging.getLogger(__name__)


def admin_url(obj):
    opts = obj._meta
    path = reverse(f"admin:{opts.app_label}_{opts.model_name}_change", args=[obj.pk])
    return settings.SITE_URL + path


def _deliver(subject, body, recipients):
    try:
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, recipients, fail_silently=False)
    except Exception:  # an alert must never break the request that triggered it
        logger.exception("Could not send a staff notification: %s", subject)


def notify_staff(subject, lines, obj):
    """Send after the current transaction commits, without slowing the request down."""
    recipients = settings.STAFF_NOTIFICATION_EMAILS
    if not recipients:
        return
    body = "\n".join([*filter(None, lines), "", f"Open in MoFirms staff: {admin_url(obj)}", "",
                      "This is an automatic alert. Personal details are only shown in /staff/."])
    full_subject = f"[MoFirms] {subject}"

    def send():
        if settings.STAFF_NOTIFICATIONS_ASYNC:
            threading.Thread(target=_deliver, args=(full_subject, body, recipients), daemon=True).start()
        else:
            _deliver(full_subject, body, recipients)

    transaction.on_commit(send)


def _channel(obj):
    preferred = getattr(obj, "preferred_contact", "")
    return "WhatsApp" if preferred == "whatsapp" else "website"


NEW_RECORD_LABELS = {
    FarmerProfile: "farmer registration",
    PartnerProfile: "supplier/buyer registration",
    ConsultationLead: "consultation request",
    FinancialAnalysisRequest: "financial analysis request",
    RiskAssessmentRequest: "risk assessment request",
    ResearcherApplication: "researcher application",
}


@receiver(post_save, sender=FarmerProfile)
@receiver(post_save, sender=PartnerProfile)
@receiver(post_save, sender=ConsultationLead)
@receiver(post_save, sender=FinancialAnalysisRequest)
@receiver(post_save, sender=RiskAssessmentRequest)
@receiver(post_save, sender=ResearcherApplication)
def alert_new_record(sender, instance, created, raw=False, **kwargs):
    if not created or raw:
        return
    label = NEW_RECORD_LABELS[sender]
    reference = getattr(instance, "public_reference", "")
    if sender is ResearcherApplication:
        # WhatsApp applicants get an account without a password until staff approve them.
        channel = "website" if instance.user.has_usable_password() else "WhatsApp"
    else:
        channel = _channel(instance)
    subject = f"New {label}" + (f" {reference}" if reference else "") + f" (via {channel})"
    notify_staff(subject, [f"A new {label} has arrived via {channel}.",
                           f"Reference: {reference}" if reference else ""], instance)


def alert_whatsapp(contact: WhatsAppContact, kind):
    subjects = {
        "help": "WhatsApp callback requested",
        "deletion": "WhatsApp data deletion requested",
        "reply": "WhatsApp message waiting for a staff reply",
    }
    lines = {
        "help": "Someone asked the MoFirms team to call them back.",
        "deletion": "Someone asked MoFirms to delete their data. Confirm it is them before deleting.",
        "reply": "Someone replied to a staff message on WhatsApp. Free-text replies are allowed for 24 hours.",
    }
    notify_staff(subjects[kind], [lines[kind]], contact)
