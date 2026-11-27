"""WhatsApp chat versions of the partner, financial analysis, risk assessment and
researcher application forms.

Each chat asks the same questions as the web form, one at a time. Answers are held on the
WhatsAppContact until the person agrees at the end; only then is the record created, so a
cancelled chat leaves nothing half-submitted. Documents still go through the website, and
researchers never type a password into WhatsApp: once approved they get a one-time link
to set it on the website.
"""

from datetime import timedelta

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.utils import timezone

from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.db import transaction
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from .forms import FinancialAnalysisRequestForm, PartnerRegistrationForm, RiskAssessmentRequestForm
from .models import (
    PARTNER_DELIVERY_CHOICES,
    PARTNER_OFFER_CHOICES,
    PARTNER_ROLE_CHOICES,
    PRODUCE_CATEGORY_CHOICES,
    FinancialAnalysisRequest,
    PartnerProfile,
    ResearcherApplication,
    RiskAssessmentRequest,
)
from .templatetags.custom_i18n import translate
from .whatsapp_details import NO_WORDS, SKIP_WORDS, YES_WORDS, _parse

MAX_SUBMISSIONS_PER_DAY = 3
LONG_TEXT_LIMIT = 1500


def _step(key, kind, model, *, choices=None, prefix=None, section=None, when=None,
          required=False, low=None, high=None):
    limit = None
    if kind == "text":
        field = model._meta.get_field(key)
        limit = field.max_length or LONG_TEXT_LIMIT
    return {
        "key": key, "field": key, "kind": kind, "choices": choices, "prefix": prefix,
        "section": section, "when": when, "required": required, "limit": limit,
        "low": low, "high": high,
    }


def _has_role(role):
    return lambda answers: role in answers.get("roles", [])


def _is_business(answers):
    return answers.get("applicant_type") == "business"


PP = PartnerProfile
_PF = PartnerRegistrationForm.base_fields


def _p(key, kind, **kwargs):
    return _step(key, kind, PP, **kwargs)


PARTNER_STEPS = [
    _p("applicant_type", "choice", choices=PP.ApplicantType.choices,
       prefix="choice.applicant_type.partner", section="about", required=True),
    _p("contact_name", "text", required=True),
    _p("business_name", "text", required=_is_business),
    _p("trading_name", "text"),
    _p("business_description", "text"),
    _p("roles", "multi", choices=PARTNER_ROLE_CHOICES, prefix="choice.partner_role", required=True),
    _p("email", "email"),
    _p("website", "url"),
    _p("registration_status", "choice", choices=PP.RegistrationStatus.choices,
       prefix="choice.registration_status", section="business"),
    _p("registration_number", "text"),
    _p("year_established", "int", low=1800, high=timezone.now().year),
    _p("years_experience", "choice", choices=PP.Experience.choices, prefix="choice.experience"),
    _p("business_size", "choice", choices=PP.BusinessSize.choices, prefix="choice.business_size"),
    _p("staff_band", "choice", choices=PP.StaffBand.choices, prefix="choice.staff_band"),
    _p("county", "county", section="location", required=True),
    _p("sub_county", "text"),
    _p("ward", "text"),
    _p("operating_counties", "counties"),
    _p("delivery_methods", "multi", choices=PARTNER_DELIVERY_CHOICES, prefix="choice.partner_delivery"),
    _p("offer_categories", "multi", choices=PARTNER_OFFER_CHOICES, prefix="choice.partner_offer",
       section="supplier", when=_has_role("supplier"), required=True),
    _p("offer_details", "text", when=_has_role("supplier"), required=True),
    _p("brands_or_products", "text", when=_has_role("supplier")),
    _p("service_area", "text", when=_has_role("supplier")),
    _p("lead_time", "text", when=_has_role("supplier")),
    _p("minimum_order", "text", when=_has_role("supplier")),
    _p("prices_and_terms", "text", when=_has_role("supplier")),
    _p("produce_categories", "multi", choices=PRODUCE_CATEGORY_CHOICES, prefix="choice.produce_category",
       section="buyer", when=_has_role("buyer"), required=True),
    _p("produce_details", "text", when=_has_role("buyer"), required=True),
    _p("sourcing_counties", "counties", when=_has_role("buyer")),
    _p("buyer_capacity", "choice", choices=PP.CapacityBand.choices, prefix="choice.capacity_band",
       when=_has_role("buyer")),
    _p("buying_frequency", "text", when=_has_role("buyer")),
    _p("quality_requirements", "text", when=_has_role("buyer")),
    _p("payment_terms", "text", when=_has_role("buyer")),
    _p("service_description", "text", section="service", when=_has_role("service_provider"),
       required=True),
    _p("service_capacity", "choice", choices=PP.CapacityBand.choices, prefix="choice.capacity_band",
       when=_has_role("service_provider")),
    _p("staff_qualifications", "text", when=_has_role("service_provider")),
    _p("clients_and_references", "text", section="goals"),
    _p("licences_and_standards", "text"),
    _p("engagement_interests", "multi", choices=_PF["engagement_interests"].choices,
       prefix="choice.partner_engagement"),
    _p("challenges", "multi", choices=_PF["challenges"].choices, prefix="choice.partner_challenge"),
    _p("partnership_goals", "text"),
    _p("additional_notes", "text"),
    _p("listing_consent", "yes_no", section="consent"),
    _p("research_invite", "yes_no"),
    _p("consent", "consent"),
]

FA = FinancialAnalysisRequest
_FF = FinancialAnalysisRequestForm.base_fields


def _f(key, kind, **kwargs):
    return _step(key, kind, FA, **kwargs)


FINANCE_STEPS = [
    _f("applicant_type", "choice", choices=FA.ApplicantType.choices,
       prefix="choice.applicant_type.general", section="about", required=True),
    _f("contact_name", "text", required=True),
    _f("business_name", "text", required=_is_business),
    _f("email", "email"),
    _f("county", "county", required=True),
    _f("sector", "text"),
    _f("services_requested", "multi", choices=_FF["services_requested"].choices,
       prefix="choice.financial_service", section="request", required=True),
    _f("financial_period", "text"),
    _f("records_available", "multi", choices=_FF["records_available"].choices,
       prefix="choice.records_available"),
    _f("accounting_software", "text"),
    _f("annual_revenue_band", "choice", choices=FA.RevenueBand.choices, prefix="choice.revenue_band"),
    _f("funding_need_band", "choice", choices=FA.FundingNeedBand.choices, prefix="choice.funding_need"),
    _f("timeline", "choice", choices=FA.Timeline.choices, prefix="choice.timeline"),
    _f("request_summary", "text", required=True),
    _f("consent", "consent", section="consent"),
]

RA = RiskAssessmentRequest
_RF = RiskAssessmentRequestForm.base_fields


def _r(key, kind, **kwargs):
    return _step(key, kind, RA, **kwargs)


RISK_STEPS = [
    _r("applicant_type", "choice", choices=RA.ApplicantType.choices,
       prefix="choice.applicant_type.general", section="about", required=True),
    _r("contact_name", "text", required=True),
    _r("business_name", "text", required=_is_business),
    _r("email", "email"),
    _r("county", "county", required=True),
    _r("sector", "text"),
    _r("enterprise_stage", "choice", choices=RA.EnterpriseStage.choices, prefix="choice.enterprise_stage"),
    _r("assessment_areas", "multi", choices=_RF["assessment_areas"].choices,
       prefix="choice.assessment_area", section="scope", required=True),
    _r("risk_priorities", "multi", choices=_RF["risk_priorities"].choices,
       prefix="choice.risk_priority", required=True),
    _r("opportunity_priorities", "multi", choices=_RF["opportunity_priorities"].choices,
       prefix="choice.opportunity_priority", required=True),
    _r("time_horizon", "choice", choices=RA.TimeHorizon.choices, prefix="choice.time_horizon",
       required=True),
    _r("request_summary", "text", required=True),
    _r("consent", "consent", section="consent"),
]

RS = ResearcherApplication


def _is_student(answers):
    return answers.get("applicant_type") == RS.ApplicantType.STUDENT


def _rs(key, kind, **kwargs):
    return _step(key, kind, RS, **kwargs)


RESEARCH_STEPS = [
    _rs("applicant_type", "choice", choices=RS.ApplicantType.choices,
        prefix="choice.researcher_applicant_type", section="about", required=True),
    _rs("organisation_name", "text", required=True),
    _rs("role_title", "text"),
    _rs("email", "new_email", required=True),
    _rs("website", "url"),
    _rs("country", "text"),
    _rs("supervisor_name", "text", when=_is_student, required=True),
    _rs("supervisor_email", "email", when=_is_student, required=True),
    _rs("research_purpose", "text", section="research", required=True),
    _rs("methods_summary", "text", required=True),
    _rs("privacy_policy_url", "url"),
    _rs("data_protection_contact", "text"),
    _rs("consent", "consent", section="consent"),
]

FORMS = {
    "partner": {"steps": PARTNER_STEPS, "keys": "wa.pf", "model": PartnerProfile},
    "finance": {"steps": FINANCE_STEPS, "keys": "wa.ff", "model": FinancialAnalysisRequest},
    "risk": {"steps": RISK_STEPS, "keys": "wa.rf", "model": RiskAssessmentRequest},
    "research": {"steps": RESEARCH_STEPS, "keys": "wa.rs", "model": ResearcherApplication},
}


def _applies(step, answers):
    return step["when"] is None or step["when"](answers)


def _required(step, answers):
    required = step["required"]
    return required(answers) if callable(required) else required


def _options(step, lang):
    return "\n".join(
        f"{index} - " + translate(f"{step['prefix']}.{value}", lang)
        for index, (value, _) in enumerate(step["choices"], start=1)
    )


def _prompt(spec, index, answers, lang):
    steps = spec["steps"]
    step = steps[index]
    parts = []
    if step["section"]:
        # Count only the parts this person will see (e.g. buyer questions only for buyers).
        sections = [s["section"] for s in steps if s["section"] and _applies(s, answers)]
        parts.append(translate("wa.fd.section", lang, number=sections.index(step["section"]) + 1,
                               total=len(sections),
                               title=translate(f"{spec['keys']}.section.{step['section']}", lang)))
    parts.append(translate(f"{spec['keys']}.{step['key']}", lang))
    if step["choices"]:
        parts.append(_options(step, lang))
    if step["kind"] not in {"yes_no", "consent"} and not _required(step, answers):
        parts.append(translate("wa.ff.skip_hint", lang))
    return "\n".join(parts)


def _advance(contact, spec, index, lang):
    steps = spec["steps"]
    for next_index in range(index + 1, len(steps)):
        if _applies(steps[next_index], contact.answers):
            contact.step = steps[next_index]["key"]
            return _prompt(spec, next_index, contact.answers, lang)
    raise AssertionError("Every form ends with a consent step.")


def recent_submissions(name, phone):
    since = timezone.now() - timedelta(days=1)
    return FORMS[name]["model"].objects.filter(phone="+" + phone, created_at__gte=since).count()


def start_form(contact, name, lang):
    spec = FORMS[name]
    if recent_submissions(name, contact.phone) >= MAX_SUBMISSIONS_PER_DAY:
        return translate("wa.form_limit", lang)
    contact.flow, contact.answers = name, {}
    contact.step = spec["steps"][0]["key"]
    return translate(f"{spec['keys']}.intro", lang) + "\n\n" + _prompt(spec, 0, contact.answers, lang)


def _match_county(text):
    from .whatsapp import match_county

    return match_county(text)


def _parse_extra(step, text, lang):
    """Parse the kinds only these forms use. Returns (value, error) or None to fall through."""
    kind = step["kind"]
    if kind == "county":
        county = _match_county(text)
        return (county, None) if county else (None, translate("wa.invalid_county", lang))
    if kind == "counties":
        names = [part for part in text.replace(" and ", ",").replace(" na ", ",").split(",") if part.strip()]
        matched = [_match_county(part) for part in names]
        if not names or None in matched:
            return None, translate("wa.ff.invalid_counties", lang)
        return list(dict.fromkeys(matched)), None
    if kind == "new_email":
        value, error = _parse({**step, "kind": "email"}, text, lang)
        if value and _email_taken(value):
            return None, translate("wa.rs.email_taken", lang)
        return value, error
    if kind == "int":
        digits = text.strip()
        if not digits.isdigit() or not step["low"] <= int(digits) <= step["high"]:
            return None, translate("wa.ff.invalid_year", lang, low=step["low"], high=step["high"])
        return int(digits), None
    if kind == "url":
        url = text.strip()
        if "://" not in url:
            url = "https://" + url
        try:
            URLValidator(schemes=["http", "https"])(url)
        except ValidationError:
            return None, translate("wa.ff.invalid_url", lang)
        if len(url) > PP._meta.get_field("website").max_length:
            return None, translate("wa.ff.invalid_url", lang)
        return url, None
    return None


def _email_taken(email):
    users = get_user_model().objects
    return users.filter(email__iexact=email).exists() or users.filter(username__iexact=email).exists()


def _common(contact, now):
    return {
        "phone": "+" + contact.phone,
        "preferred_contact": "whatsapp",
        "contact_consent_at": now,
        "last_contact_at": now,
    }


def _create_partner(answers, contact, lang, now):
    listing = answers.pop("listing_consent", False)
    research = answers.pop("research_invite", False)
    record = PartnerProfile(
        **answers, **_common(contact, now),
        preferred_language="Kiswahili" if lang == "sw" else "English",
        listing_referral_consent_at=now if listing else None,
        research_invite_consent_at=now if research else None,
    )
    if not record.registration_status or (
        record.applicant_type == PP.ApplicantType.INDIVIDUAL and not record.business_name
    ):
        record.registration_status = PP.RegistrationStatus.NOT_REGISTERED
    return record


def _create_finance(answers, contact, lang, now):
    return FinancialAnalysisRequest(**answers, **_common(contact, now), request_type=FA.RequestType.GENERAL)


def _create_risk(answers, contact, lang, now):
    return RiskAssessmentRequest(**answers, **_common(contact, now))


def _create_research(answers, contact, lang, now):
    """Same as the web form, except the account has no password until staff approve it."""
    email = answers.pop("email")
    if _email_taken(email):
        raise ValidationError({"email": "taken"})
    user = get_user_model()(
        username=email, email=email, first_name=answers["organisation_name"][:150], is_active=False
    )
    user.set_unusable_password()
    user.save()
    answers.setdefault("country", "Kenya")
    return ResearcherApplication(user=user, phone="+" + contact.phone, consent_at=now, last_contact_at=now, **answers)


CREATORS = {
    "partner": _create_partner,
    "finance": _create_finance,
    "risk": _create_risk,
    "research": _create_research,
}


def _create(name, contact, lang):
    now = timezone.now()
    try:
        with transaction.atomic():
            record = CREATORS[name](dict(contact.answers), contact, lang, now)
            record.full_clean()
            record.save()
    except ValidationError as error:
        if name == "research" and "email" in getattr(error, "message_dict", {}):
            # Someone registered this email while the chat was open; ask for another.
            contact.step = "email"
            return translate("wa.rs.email_taken", lang), False
        raise
    if name == "research":
        return translate("wa.rs.received", lang), True
    return translate(f"{FORMS[name]['keys']}.received", lang, reference=record.public_reference), True


SITE = "https://mofirm.co.ke"


def set_password_url(user):
    path = reverse(
        "researcher_set_password",
        args=[urlsafe_base64_encode(force_bytes(user.pk)), default_token_generator.make_token(user)],
    )
    return SITE + path


def research_entry(contact, lang):
    """Option 5: apply, check an application, or get the set-password link once approved."""
    application = (
        ResearcherApplication.objects.select_related("user")
        .filter(phone="+" + contact.phone)
        .order_by("-created_at")
        .first()
    )
    if application is None:
        return start_form(contact, "research", lang)
    status = application.review_status
    if status == RS.ReviewStatus.APPROVED and application.user.is_active:
        login_url = SITE + reverse("researcher_login")
        if application.user.has_usable_password():
            return translate("wa.rs.approved_signin", lang, email=application.user.email, url=login_url)
        return translate(
            "wa.rs.approved_link", lang, email=application.user.email, url=set_password_url(application.user)
        )
    return translate(
        "wa.rs.status", lang,
        organisation=application.organisation_name,
        status=translate(f"wa.rs.status.{status}", lang),
    )


def form_step(contact, text, lang):
    name = contact.flow
    spec = FORMS[name]
    keys = [step["key"] for step in spec["steps"]]
    if contact.step not in keys:
        contact.flow, contact.step, contact.answers = "", "", {}
        return translate("wa.menu", lang)
    index = keys.index(contact.step)
    step = spec["steps"][index]
    word = text.strip().lower()

    if step["kind"] == "consent":
        if word not in YES_WORDS:
            return translate("wa.invalid_consent", lang)
        reply, created = _create(name, contact, lang)
        if created:
            contact.flow, contact.step, contact.answers = "", "", {}
        return reply

    if step["kind"] == "yes_no":
        if word in YES_WORDS | NO_WORDS:
            contact.answers[step["key"]] = word in YES_WORDS
            return _advance(contact, spec, index, lang)
        return translate("wa.fd.yes_or_no", lang)

    if word in SKIP_WORDS:
        if _required(step, contact.answers):
            return translate("wa.fd.required", lang)
        return _advance(contact, spec, index, lang)

    value, error = _parse_extra(step, text, lang) or _parse(step, text, lang)
    if value is None:
        return error
    contact.answers[step["field"]] = value
    if step["key"] == "applicant_type" and value != "business":
        contact.answers.pop("business_name", None)
    return _advance(contact, spec, index, lang)
