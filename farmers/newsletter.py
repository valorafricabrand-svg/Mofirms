import logging
import re

from django.conf import settings
from django.core.mail import EmailMultiAlternatives, get_connection
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone

from . import gemini
from .models import NewsletterIssue, NewsletterSubscription

logger = logging.getLogger(__name__)

DRAFT_PROMPT = (
    "You write short email newsletters for MoFirms (Marks Organic Farms Concepts Limited), "
    "which supports farmers, entrepreneurs and agribusinesses in Kenya. Write in clear, "
    "friendly, practical English for small-scale farmers and business owners.\n"
    "Rules:\n"
    "- Use ONLY the facts, figures, dates and links in the staff notes. Never invent prices, "
    "statistics, events, programmes, quotes or links.\n"
    "- If the notes are thin, add general practical advice only, and put [CHECK] after any "
    "sentence staff should verify.\n"
    "- Plain text only: no markdown, no asterisks, no hashtags. Short paragraphs; simple "
    "lines starting with '- ' are fine for lists.\n"
    "- 150 to 350 words. End by inviting readers to reply or visit mofirm.co.ke.\n"
    "- Start your answer with one line 'SUBJECT: ' followed by a subject under 80 "
    "characters, then a blank line, then the newsletter body."
)


def topic_labels(topics):
    labels = dict(NewsletterSubscription.Topic.choices)
    return [labels.get(topic, topic) for topic in topics]


def draft_issue(issue):
    """Fill the issue's subject and body with an AI draft built from its notes."""
    prompt = (
        f"Topics: {', '.join(topic_labels(issue.topics)) or 'General MoFirms update'}\n\n"
        f"Staff notes:\n{issue.notes.strip() or '(none provided)'}"
    )
    text = gemini.generate(
        [{"role": "user", "parts": [{"text": prompt}]}],
        DRAFT_PROMPT,
        max_output_tokens=1200,
        temperature=0.5,
        timeout=30,
    )
    match = re.match(r"\s*SUBJECT:\s*(.+?)\s*\n(.*)", text, re.DOTALL | re.IGNORECASE)
    if match:
        issue.subject = match.group(1).strip()[:150]
        issue.body = match.group(2).strip()
    else:
        issue.body = text.strip()
    issue.ai_drafted_at = timezone.now()
    issue.save(update_fields=["subject", "body", "ai_drafted_at", "updated_at"])


def send_issue(issue, build_absolute_uri):
    """Email an approved issue to every active subscriber of its topics."""
    recipients = issue.recipients()
    sent = failed = 0
    connection = get_connection()
    connection.open()
    try:
        for subscription in recipients:
            unsubscribe_url = build_absolute_uri(
                reverse("unsubscribe_newsletter", args=[subscription.unsubscribe_token])
            )
            context = {"issue": issue, "unsubscribe_url": unsubscribe_url}
            message = EmailMultiAlternatives(
                subject=issue.subject,
                body=render_to_string("farmers/newsletter_email.txt", context),
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[subscription.email],
                reply_to=[settings.MOFIRMS_CONTACT_EMAIL],
                headers={"List-Unsubscribe": f"<{unsubscribe_url}>"},
                connection=connection,
            )
            message.attach_alternative(
                render_to_string("farmers/newsletter_email.html", context), "text/html"
            )
            try:
                message.send()
                sent += 1
            except Exception:
                logger.exception("Could not send newsletter %s to a subscriber.", issue.pk)
                failed += 1
    finally:
        connection.close()
    issue.status = NewsletterIssue.Status.SENT
    issue.sent_at = timezone.now()
    issue.recipient_count = sent
    issue.failed_count = failed
    issue.save(update_fields=["status", "sent_at", "recipient_count", "failed_count", "updated_at"])
    return sent, failed
