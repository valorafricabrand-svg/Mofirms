"""Staff conversations on WhatsApp, sent from /staff/.

When staff message someone, the bot steps aside for STAFF_MODE so their replies reach
staff instead of the menu; they can send MENU to get the bot back. WhatsApp only allows
free-text messages within 24 hours of the person's last message. Outside that window the
reply is queued and delivered the moment they next write in, and (if an approved
template is configured) a template nudges them to write.
"""

from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from .models import WhatsAppContact, WhatsAppMessage
from .notifications import alert_whatsapp
from .templatetags.custom_i18n import translate

STAFF_MODE = timedelta(hours=72)
M = WhatsAppMessage


def _send(contact, message):
    from .whatsapp import send_text

    ok, detail = send_text(contact.phone, message.body)
    message.status = M.Status.SENT if ok else M.Status.FAILED
    message.error = detail[:300]
    message.sent_at = timezone.now() if ok else None
    return ok


def staff_send(contact: WhatsAppContact, body, user):
    """Send (or queue) a staff reply. Returns the saved WhatsAppMessage."""
    from .whatsapp import send_template

    now = timezone.now()
    message = M(contact=contact, direction=M.Direction.OUTBOUND, body=body.strip(), sent_by=user)
    if contact.can_send_free_text:
        _send(contact, message)
    else:
        already_waiting = contact.messages.filter(status=M.Status.QUEUED).exists()
        message.status = M.Status.QUEUED
        template = settings.WHATSAPP_FOLLOWUP_TEMPLATE
        if template and not already_waiting:
            ok, detail = send_template(contact.phone, template, settings.WHATSAPP_FOLLOWUP_TEMPLATE_LANGUAGE)
            if not ok:
                message.error = f"Template not sent: {detail}"[:300]
    message.save()
    if message.status != M.Status.FAILED:
        contact.staff_until = now + STAFF_MODE
        contact.reply_needed_at = None
        contact.save(update_fields=["staff_until", "reply_needed_at", "updated_at"])
    return message


def deliver_queued(contact):
    """Called when the person writes in: the 24-hour window is open again."""
    queued = list(contact.messages.filter(status=M.Status.QUEUED).order_by("created_at"))
    for message in queued:
        _send(contact, message)
        message.save(update_fields=["status", "error", "sent_at"])
    if queued:
        contact.staff_until = timezone.now() + STAFF_MODE
    return len(queued)


def in_staff_mode(contact):
    return bool(contact.staff_until and contact.staff_until > timezone.now())


def receive_for_staff(contact, text, lang):
    """Store a message meant for staff. Returns the bot's reply, or None to stay quiet."""
    M.objects.create(
        contact=contact, direction=M.Direction.INBOUND, body=text[:4096], status=M.Status.RECEIVED
    )
    if contact.reply_needed_at:
        return None  # staff already know; don't repeat the acknowledgement
    contact.reply_needed_at = timezone.now()
    alert_whatsapp(contact, "reply")
    return translate("wa.staff_ack", lang)
