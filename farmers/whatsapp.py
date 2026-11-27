import hashlib
import hmac
import json
import logging
import re
import secrets
import urllib.error
import urllib.request
from datetime import timedelta

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model, login
from django.contrib.auth.hashers import check_password, make_password
from django.core.cache import cache
from django.db import transaction
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import ACTIVITY_CHOICES, COUNTIES, ConsultationLead, FarmerProfile, WhatsAppContact
from .templatetags.custom_i18n import current_lang, translate
from .views import _rate_limit_reached
from .whatsapp_details import farm_details_step, start_farm_details
from .whatsapp_forms import FORMS as CHAT_FORMS
from .whatsapp_forms import form_step, research_entry, start_form
from .whatsapp_books import books_step, start_books

logger = logging.getLogger(__name__)

MAX_CODE_ATTEMPTS = 5
LOCK_MINUTES = 15
UNLOCK_MINUTES = 30

MENU_WORDS = {"hi", "hello", "hey", "menu", "start", "habari", "mambo"}
CANCEL_WORDS = {"cancel", "stop", "acha", "sitisha"}
YES_WORDS = {"yes", "y", "ndio", "ndiyo", "sawa"}
LANGUAGE_WORDS = {"0", "language", "lugha"}
STATUS_WORDS = {"6", "status", "hali"}
DETAILS_WORDS = {"7", "details", "taarifa"}
NEW_CODE_WORDS = {"8", "code", "new code", "nambari"}
HELP_WORDS = {"9", "help", "msaada"}
FORM_FLOWS = {"2": "partner", "3": "finance", "4": "risk"}
RESEARCH_WORDS = {"5", "research", "utafiti"}
FREE_TEXT_FLOWS = {"consult", "farm", "books", *CHAT_FORMS}
BOOKS_WORDS = {"11", "smarthasibu", "smart hasibu", "hasibu", "books", "hesabu"}
CONSULT_WORDS = {"10", "consult", "consultation", "ushauri"}
SKIP_WORDS = {"skip", "ruka"}
MAX_CONSULTATIONS_PER_DAY = 3
MIN_MESSAGE_LENGTH = 10
MAX_MESSAGE_LENGTH = ConsultationLead._meta.get_field("message").max_length


def normalize_phone(raw):
    """Return Kenyan/international numbers as digits only, e.g. 254712345678."""
    digits = re.sub(r"\D", "", raw or "")
    if digits.startswith("0") and len(digits) == 10:
        return "254" + digits[1:]
    if len(digits) == 9 and digits[0] in "17":
        return "254" + digits
    return digits



def whatsapp_configured():
    return all(
        (
            settings.WHATSAPP_ACCESS_TOKEN,
            settings.WHATSAPP_PHONE_NUMBER_ID,
            settings.WHATSAPP_APP_SECRET,
            settings.WHATSAPP_VERIFY_TOKEN,
        )
    )


def send_text(phone, body):
    url = (
        f"https://graph.facebook.com/{settings.WHATSAPP_GRAPH_VERSION}/"
        f"{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
    )
    payload = json.dumps(
        {
            "messaging_product": "whatsapp",
            "to": phone,
            "type": "text",
            "text": {"body": body[:4096]},
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=10):
            pass
    except (urllib.error.URLError, TimeoutError) as exc:
        detail = exc.read().decode("utf-8", "ignore")[:300] if isinstance(exc, urllib.error.HTTPError) else str(exc)
        logger.warning("WhatsApp send failed: %s", detail)


def issue_code(contact):
    code = f"{secrets.randbelow(10**6):06d}"
    contact.code_hash = make_password(code)
    contact.code_set_at = timezone.now()
    contact.failed_attempts = 0
    contact.locked_until = None
    contact.unlocked_until = timezone.now() + timedelta(minutes=UNLOCK_MINUTES)
    return code


def verify_code(contact, code):
    """Check a code against a contact. Returns "ok", "wrong" or "locked"."""
    now = timezone.now()
    if contact.locked_until and contact.locked_until > now:
        return "locked"
    if contact.code_hash and check_password(code, contact.code_hash):
        contact.failed_attempts = 0
        contact.locked_until = None
        return "ok"
    contact.failed_attempts += 1
    if contact.failed_attempts >= MAX_CODE_ATTEMPTS:
        contact.failed_attempts = 0
        contact.locked_until = now + timedelta(minutes=LOCK_MINUTES)
        return "locked"
    return "wrong"


def find_existing_profile(phone):
    """Match a website registration whose phone was typed with any spacing or prefix."""
    if len(phone) < 9:
        return None
    pattern = r"\D*".join(phone[-9:]) + r"\D*$"
    candidates = FarmerProfile.objects.filter(
        phone__regex=pattern, whatsapp_contact__isnull=True
    ).order_by("-created_at")
    return next((p for p in candidates if normalize_phone(p.phone) == phone), None)


def match_county(text):
    cleaned = re.sub(r"[^a-z]", "", text.lower().replace("county", "").replace("kaunti", ""))
    if not cleaned:
        return None
    keyed = {re.sub(r"[^a-z]", "", county.lower()): county for county in COUNTIES}
    if cleaned in keyed:
        return keyed[cleaned]
    matches = [county for key, county in keyed.items() if key.startswith(cleaned)]
    return matches[0] if len(matches) == 1 else None


def activity_options(lang):
    return "\n".join(
        f"{index} - {translate(f'choice.activity.{value}', lang)}"
        for index, (value, _) in enumerate(ACTIVITY_CHOICES, start=1)
    )


def parse_activities(text):
    numbers = [int(n) for n in re.findall(r"\d+", text)]
    if not numbers or any(n < 1 or n > len(ACTIVITY_CHOICES) for n in numbers):
        return None
    return [ACTIVITY_CHOICES[n - 1][0] for n in dict.fromkeys(numbers)]


def _review_notice(profile, lang):
    """The same review banner the web dashboard shows, as WhatsApp text."""
    state = {
        FarmerProfile.VerificationStatus.VERIFIED: "reviewed",
        FarmerProfile.VerificationStatus.FOLLOW_UP: "follow_up",
    }.get(profile.verification_status, "under_review")
    lines = [
        f"*{translate(f'farmers.farmer_dashboard.{state}_title', lang)}*",
        translate(f"farmers.farmer_dashboard.{state}_body", lang),
    ]
    # Staff notes are only shared when they ask the farmer for something, as on the web.
    if state == "follow_up" and profile.verification_notes.strip():
        lines.append(translate("wa.follow_up_notes", lang, notes=profile.verification_notes.strip()))
    return "\n".join(lines)


def status_reply(profile, lang):
    return _review_notice(profile, lang) + "\n\n" + translate(
        "wa.status",
        lang,
        reference=profile.public_reference,
        status=translate(f"wa.status.{profile.verification_status}", lang),
        submitted=timezone.localtime(profile.created_at).strftime("%d %b %Y"),
    )


def _documents_section(profile, lang):
    documents = profile.documents.all()
    if not documents:
        return translate("farmers.farmer_dashboard.no_documents", lang)
    return "\n".join(
        "• {type} — {status}".format(
            type=translate(f"wa.doc_type.{document.document_type}", lang),
            status=translate(f"wa.doc_status.{document.review_status}", lang),
        )
        for document in documents
    )


def details_reply(profile, lang):
    activities = ", ".join(
        translate(f"choice.activity.{value}", lang) for value in profile.activities
    ) or "-"
    group = ""
    if profile.registration_type == FarmerProfile.RegistrationType.GROUP and profile.group_name:
        group = f"{translate('farmers.farmer_dashboard.group_label', lang)} {profile.group_name}\n"
    return translate(
        "wa.details",
        lang,
        notice=_review_notice(profile, lang),
        name=profile.full_name,
        group=group,
        county=profile.county,
        activities=activities,
        phone=profile.phone or "-",
        reference=profile.public_reference,
        status=translate(f"wa.status.{profile.verification_status}", lang),
        submitted=timezone.localtime(profile.created_at).strftime("%d %b %Y"),
        documents=_documents_section(profile, lang),
        financial_title=translate("farmers.farmer_dashboard.financial_title", lang),
        financial_body=translate("farmers.farmer_dashboard.financial_body", lang),
    )


def _protected_reply(contact, action, lang):
    if contact.unlocked_until and contact.unlocked_until > timezone.now():
        if action == "farm":
            return start_farm_details(contact, lang)
        if action == "books":
            return start_books(contact, lang)
        return status_reply(contact.profile, lang) if action == "status" else details_reply(contact.profile, lang)
    contact.flow, contact.step = "unlock", action
    return translate("wa.ask_code", lang)


def _finish_registration(contact, lang):
    answers = contact.answers
    now = timezone.now()
    with transaction.atomic():
        profile = FarmerProfile.objects.create(
            registration_type=FarmerProfile.RegistrationType.INDIVIDUAL,
            full_name=answers["name"],
            phone="+" + contact.phone,
            preferred_contact=FarmerProfile.ContactPreference.WHATSAPP,
            preferred_language="Kiswahili" if lang == "sw" else "English",
            county=answers["county"],
            activities=answers["activities"],
            privacy_consent_at=now,
            last_contact_at=now,
        )
        contact.profile = profile
        code = issue_code(contact)
    contact.flow, contact.step, contact.answers = "", "", {}
    return translate("wa.registered", lang, reference=profile.public_reference, code=code)


def _registration_step(contact, text, lang):
    step = contact.step
    if step == "name":
        if not 2 <= len(text) <= 180:
            return translate("wa.invalid_name", lang)
        contact.answers["name"] = text
        contact.step = "county"
        return translate("wa.ask_county", lang)
    if step == "county":
        county = match_county(text)
        if not county:
            return translate("wa.invalid_county", lang)
        contact.answers["county"] = county
        contact.step = "activities"
        return translate("wa.ask_activities", lang, options=activity_options(lang))
    if step == "activities":
        activities = parse_activities(text)
        if not activities:
            return translate("wa.invalid_activities", lang)
        contact.answers["activities"] = activities
        contact.step = "consent"
        return translate("wa.ask_consent", lang)
    if text.lower() in YES_WORDS:
        return _finish_registration(contact, lang)
    return translate("wa.invalid_consent", lang)


def consultation_options(lang):
    return "\n".join(
        f"{index} - {translate(f'choice.consultation_category.{value}', lang)}"
        for index, (value, _) in enumerate(ConsultationLead.Category.choices, start=1)
    )


def _start_consultation(contact, lang):
    since = timezone.now() - timedelta(days=1)
    if ConsultationLead.objects.filter(phone="+" + contact.phone, created_at__gte=since).count() >= MAX_CONSULTATIONS_PER_DAY:
        return translate("wa.consult_limit", lang)
    contact.flow, contact.answers = "consult", {}
    if contact.profile:
        contact.answers["name"] = contact.profile.full_name
        contact.step = "category"
        return translate("wa.consult_ask_category", lang, options=consultation_options(lang))
    contact.step = "name"
    return translate("wa.consult_ask_name", lang)


def _finish_consultation(contact, lang):
    answers = contact.answers
    now = timezone.now()
    lead = ConsultationLead.objects.create(
        full_name=answers["name"],
        phone="+" + contact.phone,
        preferred_contact=ConsultationLead.PreferredContact.WHATSAPP,
        organisation_or_county=answers.get("organisation", ""),
        category=answers["category"],
        message=answers["message"],
        privacy_consent_at=now,
        last_contact_at=now,
    )
    contact.flow, contact.step, contact.answers = "", "", {}
    return translate("wa.consult_received", lang, reference=lead.public_reference)


def _consultation_step(contact, text, lang):
    step = contact.step
    if step == "name":
        if not 2 <= len(text) <= 160:
            return translate("wa.invalid_name", lang)
        contact.answers["name"] = text
        contact.step = "category"
        return translate("wa.consult_ask_category", lang, options=consultation_options(lang))
    if step == "category":
        choices = ConsultationLead.Category.choices
        number = re.sub(r"\D", "", text)
        if not number or not 1 <= int(number) <= len(choices):
            return translate("wa.consult_invalid_category", lang)
        contact.answers["category"] = choices[int(number) - 1][0]
        contact.step = "message"
        return translate("wa.consult_ask_message", lang)
    if step == "message":
        if not MIN_MESSAGE_LENGTH <= len(text) <= MAX_MESSAGE_LENGTH:
            return translate("wa.consult_invalid_message", lang, maximum=MAX_MESSAGE_LENGTH)
        contact.answers["message"] = text
        if contact.profile:
            contact.answers["organisation"] = contact.profile.county
            contact.step = "consent"
            return translate("wa.consult_ask_consent", lang)
        contact.step = "organisation"
        return translate("wa.consult_ask_organisation", lang)
    if step == "organisation":
        if text.lower() not in SKIP_WORDS:
            contact.answers["organisation"] = text[:180]
        contact.step = "consent"
        return translate("wa.consult_ask_consent", lang)
    if text.lower() in YES_WORDS:
        return _finish_consultation(contact, lang)
    return translate("wa.invalid_consent", lang)


def _unlock_step(contact, text, lang):
    result = verify_code(contact, re.sub(r"\D", "", text))
    if result == "locked":
        contact.flow = contact.step = ""
        return translate("wa.locked", lang, minutes=LOCK_MINUTES)
    if result == "wrong":
        return translate("wa.wrong_code", lang, remaining=MAX_CODE_ATTEMPTS - contact.failed_attempts)
    contact.unlocked_until = timezone.now() + timedelta(minutes=UNLOCK_MINUTES)
    action = contact.step
    contact.flow = contact.step = ""
    return _protected_reply(contact, action, lang)


def handle_message(phone, text):
    """Process one inbound text and return the reply to send back."""
    contact, _ = WhatsAppContact.objects.get_or_create(phone=phone)
    if contact.profile is None:
        existing = find_existing_profile(phone)
        if existing:
            contact.profile = existing
    text = (text or "").strip()
    word = text.lower()

    chosen = _language_choice(word, contact.flow == "language")
    if chosen:
        contact.language, contact.language_confirmed = chosen, True
        contact.flow, contact.step, contact.answers = "", "", {}
        reply = translate("wa.language_set", chosen) + "\n\n" + translate("wa.menu", chosen)
    elif word in CANCEL_WORDS:
        contact.flow, contact.step, contact.answers = "", "", {}
        reply = translate("wa.cancelled", contact.language)
    elif contact.flow not in FREE_TEXT_FLOWS and ("delete" in word or "futa" in word):
        contact.flow, contact.step, contact.answers = "", "", {}
        contact.deletion_requested_at = timezone.now()
        reply = translate("wa.delete_request", contact.language)
    elif word in LANGUAGE_WORDS or (
        not contact.language_confirmed and contact.flow not in {"register", "unlock"} | FREE_TEXT_FLOWS
    ):
        contact.flow, contact.step, contact.answers = "language", "", {}
        reply = translate("wa.language_prompt", "en")
    elif word in MENU_WORDS:
        contact.flow, contact.step, contact.answers = "", "", {}
        reply = translate("wa.menu", contact.language)
    elif contact.flow == "register":
        reply = _registration_step(contact, text, contact.language)
    elif contact.flow in CHAT_FORMS:
        reply = form_step(contact, text, contact.language)
    elif contact.flow == "farm":
        reply = farm_details_step(contact, text, contact.language)
    elif contact.flow == "books":
        reply = books_step(contact, text, contact.language)
    elif contact.flow == "consult":
        reply = _consultation_step(contact, text, contact.language)
    elif contact.flow == "unlock" and word not in NEW_CODE_WORDS:
        reply = _unlock_step(contact, text, contact.language)
    else:
        reply = _menu_choice(contact, word)
    contact.save()
    return reply


def _language_choice(word, awaiting_choice):
    if word in {"kiswahili", "swahili"} or (awaiting_choice and word == "2"):
        return "sw"
    if word == "english" or (awaiting_choice and word == "1"):
        return "en"
    return None


def _account_action(contact, action, lang):
    """Run a code-protected action, issuing a first code to web-registered farmers."""
    if not contact.code_hash:
        code = issue_code(contact)
        return translate("wa.new_code", lang, code=code) + "\n\n" + _protected_reply(contact, action, lang)
    return _protected_reply(contact, action, lang)


def _menu_choice(contact, word):
    lang = contact.language
    contact.flow = contact.step = ""
    if word in {"1", "register", "jisajili"}:
        if contact.profile:
            return _account_action(contact, "farm", lang)
        contact.flow, contact.step, contact.answers = "register", "name", {}
        return translate("wa.ask_name", lang)
    if word in FORM_FLOWS:
        return start_form(contact, FORM_FLOWS[word], lang)
    if word in RESEARCH_WORDS:
        return research_entry(contact, lang)
    if word in STATUS_WORDS | DETAILS_WORDS:
        if not contact.profile:
            return translate("wa.not_registered", lang)
        return _account_action(contact, "status" if word in STATUS_WORDS else "details", lang)
    if word in BOOKS_WORDS:
        # Registered farmers get a first code here if they have none; others get one
        # when they agree to open their SmartHasibu records.
        if contact.code_hash or contact.profile:
            return _account_action(contact, "books", lang)
        return start_books(contact, lang)
    if word in NEW_CODE_WORDS:
        if not contact.profile and not contact.code_hash:
            return translate("wa.not_registered", lang)
        return translate("wa.new_code", lang, code=issue_code(contact))
    if word in CONSULT_WORDS:
        return _start_consultation(contact, lang)
    if word in HELP_WORDS:
        contact.help_requested_at = timezone.now()
        return translate("wa.help", lang)
    return translate("wa.menu", lang)


def _valid_signature(request):
    header = request.headers.get("X-Hub-Signature-256", "")
    expected = "sha256=" + hmac.new(
        settings.WHATSAPP_APP_SECRET.encode("utf-8"), request.body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, header)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def webhook(request):
    if not whatsapp_configured():
        return HttpResponse(status=503)
    if request.method == "GET":
        if (
            request.GET.get("hub.mode") == "subscribe"
            and hmac.compare_digest(request.GET.get("hub.verify_token", ""), settings.WHATSAPP_VERIFY_TOKEN)
        ):
            return HttpResponse(request.GET.get("hub.challenge", ""), content_type="text/plain")
        return HttpResponseForbidden()

    if not _valid_signature(request):
        return HttpResponseForbidden()
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponse(status=400)

    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            for message in change.get("value", {}).get("messages", []):
                message_id = message.get("id", "")
                if not message_id or not cache.add(f"wa:msg:{message_id}", 1, 60 * 60 * 24):
                    continue
                phone = normalize_phone(message.get("from", ""))
                if not phone:
                    continue
                try:
                    if message.get("type") == "text":
                        reply = handle_message(phone, message.get("text", {}).get("body", ""))
                    else:
                        contact = WhatsAppContact.objects.filter(phone=phone).first()
                        reply = translate("wa.unsupported", contact.language if contact else "en")
                except Exception:
                    logger.exception("Could not handle WhatsApp message %s", message_id)
                    continue
                send_text(phone, reply)
    return HttpResponse("ok")


class WhatsAppLoginForm(forms.Form):
    phone = forms.CharField(max_length=20)
    code = forms.CharField(max_length=6, min_length=6)

    def __init__(self, *args, lang="en", **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["phone"].label = translate("farmers.wa_login.phone_label", lang)
        self.fields["phone"].widget.attrs.update({"inputmode": "tel", "autocomplete": "tel"})
        self.fields["code"].label = translate("farmers.wa_login.code_label", lang)
        self.fields["code"].widget.attrs.update(
            {"inputmode": "numeric", "autocomplete": "one-time-code", "pattern": r"\d{6}"}
        )


def _user_for_profile(profile, phone):
    if profile.user:
        return profile.user
    user, _ = get_user_model().objects.get_or_create(
        username=f"wa{phone}",
        defaults={"first_name": profile.full_name[:150]},
    )
    if user.has_usable_password():
        user.set_unusable_password()
        user.save(update_fields=["password"])
    profile.user = user
    profile.save(update_fields=["user"])
    return user


@require_http_methods(["GET", "POST"])
def whatsapp_login(request):
    lang = current_lang(request)
    if request.user.is_authenticated:
        return redirect("farmer_dashboard")
    form = WhatsAppLoginForm(request.POST or None, lang=lang)
    error = None
    if request.method == "POST":
        if _rate_limit_reached(request, "farmer-wa-login", limit=10):
            error = translate("farmers.wa_login.locked", lang)
        elif form.is_valid():
            phone = normalize_phone(form.cleaned_data["phone"])
            contact = (
                WhatsAppContact.objects.select_related("profile__user")
                .filter(phone=phone, profile__isnull=False)
                .exclude(code_hash="")
                .first()
            )
            result = verify_code(contact, form.cleaned_data["code"]) if contact else "wrong"
            if contact:
                contact.save(update_fields=["failed_attempts", "locked_until", "updated_at"])
            if result == "ok":
                user = _user_for_profile(contact.profile, phone)
                login(request, user, backend="django.contrib.auth.backends.ModelBackend")
                return redirect("farmer_dashboard")
            error = translate(
                "farmers.wa_login.locked" if result == "locked" else "farmers.wa_login.failed", lang
            )
        else:
            error = translate("farmers.wa_login.failed", lang)
    return render(request, "farmers/whatsapp_login.html", {"form": form, "error": error})
