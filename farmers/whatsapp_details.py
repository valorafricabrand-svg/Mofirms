"""WhatsApp chat version of the optional parts of the web farmer registration form.

After the quick WhatsApp registration (name, county, activities, consent), a farmer can
reply 1 to answer the rest of the web form one question at a time. Every answer is saved
to the FarmerProfile straight away, so stopping half way keeps what was already given.
Group details are the exception: they are held until the representative confirms they
are authorised, matching the web form's rule.
"""

import re
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.utils import timezone

from .forms import FarmerRegistrationForm
from .models import SUPPORT_CHOICES, FarmerProfile
from .templatetags.custom_i18n import translate

SKIP_WORDS = {"skip", "ruka"}
YES_WORDS = {"yes", "y", "ndio", "ndiyo", "sawa"}
NO_WORDS = {"no", "n", "hapana", "la"}

P = FarmerProfile
_FORM_FIELDS = FarmerRegistrationForm.base_fields
GROUP_STATUS_CHOICES = [c for c in P.RegistrationStatus.choices if c[0] != P.RegistrationStatus.NOT_APPLICABLE]


def _max_length(field):
    return P._meta.get_field(field).max_length


def _step(key, kind, field=None, choices=None, prefix=None, section=None, when=None, required=False):
    return {
        "key": key, "kind": kind, "field": field or key, "choices": choices, "prefix": prefix,
        "section": section, "when": when, "required": required,
    }


def _is_group(contact):
    return contact.answers.get("group") is not None


STEPS = [
    _step("registration_type", "choice", choices=P.RegistrationType.choices,
          prefix="choice.registration_type", section="about"),
    _step("group_name", "group_text", when=_is_group, required=True),
    _step("group_type", "group_choice", choices=P.GroupType.choices, prefix="choice.group_type",
          when=_is_group, required=True),
    _step("group_registration_status", "group_choice", choices=GROUP_STATUS_CHOICES,
          prefix="choice.registration_status", when=_is_group),
    _step("group_registration_number", "group_text", when=_is_group),
    _step("group_member_count", "group_number", when=_is_group),
    _step("representative_role", "group_text", when=_is_group),
    _step("group_authorization", "group_confirm", when=_is_group),
    _step("email", "email"),
    _step("sub_county", "text", section="location"),
    _step("ward", "text"),
    _step("local_area", "text"),
    _step("main_products", "text", section="farm"),
    _step("farm_size", "decimal"),
    _step("farm_size_unit", "choice", choices=P.AreaUnit.choices, prefix="choice.area_unit",
          when=lambda contact: contact.answers.get("farm_size_given"), required=True),
    _step("land_access", "choice", choices=P.LandAccess.choices, prefix="choice.land_access"),
    _step("years_farming", "choice", choices=P.Experience.choices, prefix="choice.experience"),
    _step("water_sources", "multi", choices=P.WaterSource.choices, prefix="choice.water_source"),
    _step("production_summary", "text"),
    _step("sales_band", "choice", choices=P.FinancialBand.choices, prefix="choice.financial_band",
          section="money"),
    _step("operating_cost_band", "choice", choices=P.FinancialBand.choices,
          prefix="choice.financial_band"),
    _step("finance_need_band", "choice", choices=P.FinancialBand.choices,
          prefix="choice.financial_band"),
    _step("record_keeping", "choice", choices=P.RecordKeeping.choices, prefix="choice.record_keeping"),
    _step("sales_channels", "multi", choices=_FORM_FIELDS["sales_channels"].choices,
          prefix="choice.sales_channel", section="markets"),
    _step("challenges", "multi", choices=_FORM_FIELDS["challenges"].choices,
          prefix="choice.farmer_challenge"),
    _step("support_interests", "multi", choices=SUPPORT_CHOICES, prefix="choice.support",
          section="goals"),
    _step("goals", "text"),
    _step("additional_notes", "text"),
    _step("research_invite", "yes_no"),
]
STEP_INDEX = {step["key"]: index for index, step in enumerate(STEPS)}
SECTIONS = [step["section"] for step in STEPS if step["section"]]
TEXT_LIMITS = {"production_summary": 1000, "goals": 1000, "additional_notes": 1000}


def _options(step, lang):
    prefix = step["prefix"]
    return "\n".join(
        f"{index} - " + translate(f"{prefix}.{value}", lang)
        for index, (value, _) in enumerate(step["choices"], start=1)
    )


def _current_value(step, profile, lang):
    """What the profile holds now, so SKIP is a clear 'keep this' choice."""
    field = step["field"]
    if step["kind"] in {"group_confirm", "yes_no"} or not hasattr(profile, field):
        return ""
    value = getattr(profile, field)
    if step["kind"] == "group_choice" and profile.registration_type != P.RegistrationType.GROUP:
        return ""
    if value in (None, "", []) or value == P.RegistrationStatus.NOT_APPLICABLE:
        return ""
    if step["kind"] == "multi":
        return ", ".join(translate(f"{step['prefix']}.{item}", lang) for item in value)
    if step["kind"] in {"choice", "group_choice"}:
        return translate(f"{step['prefix']}.{value}", lang)
    if isinstance(value, Decimal):
        return f"{value.normalize():f}"
    return str(value)


def _prompt(contact, index, lang):
    step = STEPS[index]
    parts = []
    if step["section"]:
        number = SECTIONS.index(step["section"]) + 1
        parts.append(translate("wa.fd.section", lang, number=number, total=len(SECTIONS),
                               title=translate(f"wa.fd.section.{step['section']}", lang)))
    parts.append(translate(f"wa.fd.{step['key']}", lang))
    if step["choices"]:
        parts.append(_options(step, lang))
    current = _current_value(step, contact.profile, lang)
    if current:
        parts.append(translate("wa.fd.now", lang, value=current))
    if not step["required"] and step["kind"] not in {"group_confirm", "yes_no"}:
        parts.append(translate("wa.fd.skip_hint", lang))
    return "\n".join(parts)


def _advance(contact, index, lang):
    """Move to the next step that applies, or finish."""
    for next_index in range(index + 1, len(STEPS)):
        when = STEPS[next_index]["when"]
        if when is None or when(contact):
            contact.step = STEPS[next_index]["key"]
            return _prompt(contact, next_index, lang)
    contact.flow, contact.step, contact.answers = "", "", {}
    return translate("wa.fd.done", lang)


def start_farm_details(contact, lang):
    contact.flow, contact.answers = "farm", {}
    contact.step = STEPS[0]["key"]
    return translate("wa.fd.intro", lang) + "\n\n" + _prompt(contact, 0, lang)


def _pick_one(text, choices):
    digits = re.sub(r"\D", "", text)
    if digits and 1 <= int(digits) <= len(choices):
        return choices[int(digits) - 1][0]
    return None


def _pick_many(text, choices):
    numbers = [int(n) for n in re.findall(r"\d+", text)]
    if not numbers or any(n < 1 or n > len(choices) for n in numbers):
        return None
    return [choices[n - 1][0] for n in dict.fromkeys(numbers)]


def _set_individual(profile):
    profile.registration_type = P.RegistrationType.INDIVIDUAL
    profile.group_name = ""
    profile.group_type = ""
    profile.group_registration_number = ""
    profile.group_member_count = None
    profile.representative_role = ""
    profile.group_authorization_confirmed = False
    profile.group_registration_status = P.RegistrationStatus.NOT_APPLICABLE
    profile.group_review_status = P.EvidenceStatus.NOT_APPLICABLE


def _apply_group(profile, group):
    profile.registration_type = P.RegistrationType.GROUP
    profile.group_name = group["group_name"]
    profile.group_type = group["group_type"]
    profile.group_registration_status = group.get("group_registration_status") or P.RegistrationStatus.PREFER_NOT
    profile.group_registration_number = group.get("group_registration_number", "")
    profile.group_member_count = group.get("group_member_count")
    profile.representative_role = group.get("representative_role", "")
    profile.group_authorization_confirmed = True
    if profile.group_review_status == P.EvidenceStatus.NOT_APPLICABLE:
        profile.group_review_status = P.EvidenceStatus.PENDING


def _parse(step, text, lang):
    """Return (value, error_reply). value is None when the answer was invalid."""
    kind = step["kind"]
    if kind in {"choice", "group_choice"}:
        value = _pick_one(text, step["choices"])
        return (value, None) if value else (None, translate("wa.fd.invalid_choice", lang))
    if kind == "multi":
        value = _pick_many(text, step["choices"])
        return (value, None) if value else (None, translate("wa.fd.invalid_multi", lang))
    if kind == "decimal":
        try:
            value = Decimal(text.replace(",", "").strip())
        except InvalidOperation:
            value = None
        if value is None or not value.is_finite() or not 0 < value <= 1_000_000:
            return None, translate("wa.fd.invalid_number", lang)
        return value.quantize(Decimal("0.01")), None
    if kind == "group_number":
        digits = re.sub(r"[,\s]", "", text)
        if not digits.isdigit() or not 1 <= int(digits) <= 1_000_000:
            return None, translate("wa.fd.invalid_number", lang)
        return int(digits), None
    if kind == "email":
        try:
            validate_email(text)
        except ValidationError:
            return None, translate("wa.fd.invalid_email", lang)
        return text.lower(), None
    limit = TEXT_LIMITS.get(step["field"]) or _max_length(step["field"])
    if len(text) > limit:
        return None, translate("wa.fd.too_long", lang, maximum=limit)
    return text, None


def farm_details_step(contact, text, lang):
    profile = contact.profile
    index = STEP_INDEX.get(contact.step)
    if profile is None or index is None:
        contact.flow, contact.step, contact.answers = "", "", {}
        return translate("wa.not_registered", lang)
    step = STEPS[index]
    word = text.strip().lower()
    kind = step["kind"]

    if kind == "group_confirm":
        if word in YES_WORDS:
            _apply_group(profile, contact.answers.pop("group"))
            profile.save()
        elif word in NO_WORDS:
            contact.answers.pop("group")
            return translate("wa.fd.group_not_saved", lang) + "\n\n" + _advance(contact, index, lang)
        else:
            return translate("wa.fd.yes_or_no", lang)
        return _advance(contact, index, lang)

    if kind == "yes_no":
        if word in YES_WORDS:
            profile.research_invite_consent_at = profile.research_invite_consent_at or timezone.now()
        elif word in NO_WORDS:
            profile.research_invite_consent_at = None
        elif word not in SKIP_WORDS:
            return translate("wa.fd.yes_or_no", lang)
        profile.save(update_fields=["research_invite_consent_at", "updated_at"])
        return _advance(contact, index, lang)

    if word in SKIP_WORDS:
        if step["required"]:
            return translate("wa.fd.required", lang)
        if step["key"] == "registration_type" and profile.registration_type == P.RegistrationType.GROUP:
            # Keep the existing group details as they are; don't re-ask them.
            return _advance(contact, STEP_INDEX["group_authorization"], lang)
        return _advance(contact, index, lang)

    value, error = _parse(step, text, lang)
    if value is None:
        return error

    if step["key"] == "registration_type":
        if value == P.RegistrationType.GROUP:
            contact.answers["group"] = {}
            return _advance(contact, index, lang)
        _set_individual(profile)
        profile.save()
        return _advance(contact, STEP_INDEX["group_authorization"], lang)
    if kind.startswith("group_"):
        contact.answers["group"][step["field"]] = value
        return _advance(contact, index, lang)

    setattr(profile, step["field"], value)
    if step["key"] == "farm_size":
        contact.answers["farm_size_given"] = True
    profile.save()
    return _advance(contact, index, lang)
