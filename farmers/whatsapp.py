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

from .models import ACTIVITY_CHOICES, COUNTIES, FarmerProfile, WhatsAppContact
from .templatetags.custom_i18n import current_lang, translate
from .views import _rate_limit_reached

logger = logging.getLogger(__name__)

MAX_CODE_ATTEMPTS = 5
LOCK_MINUTES = 15
UNLOCK_MINUTES = 30

MENU_WORDS = {"hi", "hello", "hey", "menu", "start", "habari", "mambo", "0"}
CANCEL_WORDS = {"cancel", "stop", "acha", "sitisha"}
YES_WORDS = {"yes", "y", "ndio", "ndiyo", "sawa"}


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


def status_reply(profile, lang):
    return translate(
        "wa.status",
        lang,
        reference=profile.public_reference,
        status=translate(f"wa.status.{profile.verification_status}", lang),
        submitted=timezone.localtime(profile.created_at).strftime("%d %b %Y"),
    )


def details_reply(profile, lang):
    activities = ", ".join(
        translate(f"choice.activity.{value}", lang) for value in profile.activities
    ) or "-"
    return translate(
        "wa.details",
        lang,
        name=profile.full_name,
        county=profile.county,
        activities=activities,
        phone=profile.phone or "-",
        reference=profile.public_reference,
    )


def _protected_reply(contact, action, lang):
    if contact.unlocked_until and contact.unlocked_until > timezone.now():
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

    if word in {"kiswahili", "swahili"}:
        contact.language = "sw"
        reply = translate("wa.language_set", "sw") + "\n\n" + translate("wa.menu", "sw")
    elif word == "english":
        contact.language = "en"
        reply = translate("wa.language_set", "en") + "\n\n" + translate("wa.menu", "en")
    elif word in CANCEL_WORDS:
        contact.flow, contact.step, contact.answers = "", "", {}
        reply = translate("wa.cancelled", contact.language)
    elif "delete" in word or "futa" in word:
        contact.flow, contact.step, contact.answers = "", "", {}
        contact.deletion_requested_at = timezone.now()
        reply = translate("wa.delete_request", contact.language)
    elif word in MENU_WORDS:
        contact.flow, contact.step, contact.answers = "", "", {}
        reply = translate("wa.menu", contact.language)
    elif contact.flow == "register":
        reply = _registration_step(contact, text, contact.language)
    elif contact.flow == "unlock" and word not in {"4", "code", "new code", "nambari"}:
        reply = _unlock_step(contact, text, contact.language)
    else:
        reply = _menu_choice(contact, word)
    contact.save()
    return reply


def _menu_choice(contact, word):
    lang = contact.language
    contact.flow = contact.step = ""
    if word in {"1", "register", "jisajili"}:
        if contact.profile:
            return translate("wa.already_registered", lang, reference=contact.profile.public_reference)
        contact.flow, contact.step, contact.answers = "register", "name", {}
        return translate("wa.ask_name", lang)
    if word in {"2", "status", "hali", "3", "details", "taarifa"}:
        if not contact.profile:
            return translate("wa.not_registered", lang)
        action = "status" if word in {"2", "status", "hali"} else "details"
        if not contact.code_hash:
            code = issue_code(contact)
            return translate("wa.new_code", lang, code=code) + "\n\n" + _protected_reply(contact, action, lang)
        return _protected_reply(contact, action, lang)
    if word in {"4", "code", "new code", "nambari"}:
        if not contact.profile:
            return translate("wa.not_registered", lang)
        return translate("wa.new_code", lang, code=issue_code(contact))
    if word in {"5", "help", "msaada"}:
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
