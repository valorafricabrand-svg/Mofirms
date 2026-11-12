import hashlib
import hmac

from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone

from .geo_zones import nearest_county
from .mpesa import MpesaError, normalize_phone_number
from .models import FarmerProfile, WhatsAppLocationPing


class WhatsAppWebhookError(Exception):
    """Raised for a malformed or unverifiable webhook request."""


def webhook_configured():
    return bool(settings.WHATSAPP_APP_SECRET and settings.WHATSAPP_VERIFY_TOKEN)


def verify_signature(raw_body, signature_header):
    """Check Meta's X-Hub-Signature-256 header against the configured app secret."""
    if not signature_header or not signature_header.startswith("sha256="):
        return False
    expected = hmac.new(
        settings.WHATSAPP_APP_SECRET.encode("utf-8"), raw_body, hashlib.sha256
    ).hexdigest()
    provided = signature_header[len("sha256="):]
    return hmac.compare_digest(expected, provided)


def extract_location_messages(payload):
    """Yield (wa_message_id, from_number, latitude, longitude) for each location
    message in a Meta WhatsApp Cloud API webhook payload. Malformed entries are
    skipped rather than raising, since one bad message should not drop the rest."""
    if not isinstance(payload, dict):
        return
    for entry in payload.get("entry", []) if isinstance(payload.get("entry"), list) else []:
        changes = entry.get("changes", []) if isinstance(entry, dict) else []
        for change in changes if isinstance(changes, list) else []:
            value = change.get("value") if isinstance(change, dict) else None
            messages = value.get("messages") if isinstance(value, dict) else None
            for message in messages if isinstance(messages, list) else []:
                if not isinstance(message, dict) or message.get("type") != "location":
                    continue
                location = message.get("location")
                wa_message_id = message.get("id")
                from_number = message.get("from")
                if not isinstance(location, dict) or not wa_message_id or not from_number:
                    continue
                latitude = location.get("latitude")
                longitude = location.get("longitude")
                if not isinstance(latitude, (int, float)) or not isinstance(longitude, (int, float)):
                    continue
                yield wa_message_id, from_number, latitude, longitude


def record_location_ping(wa_message_id, from_number, latitude, longitude):
    """Store the ping (idempotently) and, if a registration's phone number
    matches, copy the coordinates onto that FarmerProfile. Returns the ping,
    or None if this message id was already recorded."""
    try:
        normalized_sender = normalize_phone_number(from_number)
    except MpesaError:
        normalized_sender = None

    matched_profile = None
    if normalized_sender:
        # Prefer a draft awaiting step 2 (the common case: the farmer just
        # submitted step 1 and is sharing their pin now); fall back to any
        # profile with a matching phone number otherwise.
        candidates = list(
            FarmerProfile.objects.exclude(phone="")
            .filter(registration_completed_at__isnull=True)
            .order_by("-created_at")
        ) or list(
            FarmerProfile.objects.exclude(phone="").order_by("-created_at")
        )
        for profile in candidates:
            try:
                if normalize_phone_number(profile.phone) == normalized_sender:
                    matched_profile = profile
                    break
            except MpesaError:
                continue

    try:
        with transaction.atomic():
            ping = WhatsAppLocationPing.objects.create(
                wa_message_id=wa_message_id,
                phone_number=normalized_sender or from_number,
                latitude=latitude,
                longitude=longitude,
                matched_profile=matched_profile,
            )
    except IntegrityError:
        return None

    if matched_profile is not None:
        matched_profile.farm_latitude = latitude
        matched_profile.farm_longitude = longitude
        matched_profile.location_shared_at = timezone.now()
        matched_profile.county = nearest_county(float(latitude), float(longitude)) or ""
        matched_profile.save(
            update_fields=[
                "farm_latitude", "farm_longitude", "location_shared_at", "county",
            ]
        )
    return ping
