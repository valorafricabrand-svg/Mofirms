"""SmartHasibu farm records over WhatsApp (menu option 11).

Entries are saved to the same SmartHasibu ledger the website shows, under the same
account the farmer gets when signing in on the web with their WhatsApp code. The books
are private, so every action needs the WhatsApp login code (or a recent unlock), just
like viewing registration details.
"""

import re
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.db.models import Count, Q, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone

from smart_hasibu.models import CreditSettlement, FarmEnterprise, LedgerEntry, SmartHasibuAccount

from .templatetags.custom_i18n import translate
from .whatsapp_details import SKIP_WORDS, YES_WORDS

INCOME_CATEGORIES = ["sales", "livestock", "services", "other_income"]
EXPENSE_CATEGORIES = ["inputs", "labour", "transport", "storage", "utilities", "equipment", "other_expense"]
MAX_AMOUNT = Decimal("9999999999.99")
ZERO = Decimal("0.00")
MAX_LISTED = 9


# ---------------------------------------------------------------- helpers

def ksh(amount):
    amount = Decimal(amount)
    text = f"{amount:,.2f}"
    return "KSh " + (text[:-3] if text.endswith(".00") else text)


def books_user(contact, create):
    """The SmartHasibu owner for this WhatsApp number: the same user the web WhatsApp login uses."""
    from .whatsapp import _user_for_profile

    if contact.profile:
        if contact.profile.user or create:
            return _user_for_profile(contact.profile, contact.phone)
        return None
    users = get_user_model().objects
    user = users.filter(username=f"wa{contact.phone}").first()
    if user is None and create:
        user = users.create(username=f"wa{contact.phone}")
        user.set_unusable_password()
        user.save(update_fields=["password"])
    return user


def _has_account(user):
    return user is not None and SmartHasibuAccount.objects.filter(user=user).exists()


def _enterprises(user):
    return list(FarmEnterprise.objects.filter(owner=user))


def _numbered(items, lang):
    return "\n".join(f"{index} - {label}" for index, label in enumerate(items, start=1))


def _pick(text, count):
    digits = re.sub(r"\D", "", text)
    if digits and 1 <= int(digits) <= count:
        return int(digits) - 1
    return None


def parse_amount(text):
    cleaned = re.sub(r"(?i)\b(ksh|kes|sh|shillings?)\b\.?", "", text).replace(",", "").strip()
    multiplier = Decimal(1)
    if cleaned.lower().endswith("k"):
        cleaned, multiplier = cleaned[:-1], Decimal(1000)
    try:
        amount = (Decimal(cleaned) * multiplier).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError):
        return None
    if not amount.is_finite() or amount <= 0 or amount > MAX_AMOUNT:
        return None
    return amount


def parse_date(text, today):
    word = text.strip().lower()
    if word in {"1", "today", "leo"}:
        return today
    if word in {"2", "yesterday", "jana"}:
        return today - timedelta(days=1)
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y", "%d/%m", "%d-%m"):
        try:
            parsed = datetime.strptime(word, fmt).date()
        except ValueError:
            continue
        if "%Y" not in fmt and "%y" not in fmt:
            parsed = parsed.replace(year=today.year)
            if parsed > today:
                parsed = parsed.replace(year=today.year - 1)
        return parsed if parsed <= today else None
    return None


def _categories(kind):
    return INCOME_CATEGORIES if kind == LedgerEntry.EntryType.INCOME else EXPENSE_CATEGORIES


def _open_credit(user):
    entries = (
        LedgerEntry.objects.filter(enterprise__owner=user, is_credit=True, is_deleted=False)
        .annotate(settled=Coalesce(Sum("settlements__amount"), ZERO))
        .select_related("enterprise")
        .order_by("-occurred_on", "-created_at")
    )
    return [entry for entry in entries if entry.amount - entry.settled > 0][:MAX_LISTED]


def _credit_label(entry, lang):
    side = "owed_to_you" if entry.entry_type == LedgerEntry.EntryType.INCOME else "you_owe"
    return translate(
        "wa.bk.credit_line", lang,
        side=translate(f"wa.bk.{side}", lang),
        left=ksh(entry.amount - entry.settled),
        description=entry.description,
        who=f" ({entry.counterparty})" if entry.counterparty else "",
        day=entry.occurred_on.strftime("%d %b"),
    )


# ---------------------------------------------------------------- screens

def home(contact, lang, prefix=""):
    contact.flow, contact.step = "books", "home"
    contact.answers = {}
    text = translate("wa.bk.home", lang)
    return f"{prefix}\n\n{text}" if prefix else text


def summary_reply(user, lang):
    today = timezone.localdate()
    start = today.replace(day=1)
    entries = LedgerEntry.objects.filter(enterprise__owner=user, is_deleted=False)
    month = entries.filter(occurred_on__gte=start, occurred_on__lte=today).aggregate(
        income=Coalesce(Sum("amount", filter=Q(entry_type=LedgerEntry.EntryType.INCOME)), ZERO),
        expenses=Coalesce(Sum("amount", filter=Q(entry_type=LedgerEntry.EntryType.EXPENSE)), ZERO),
        count=Count("pk"),
    )
    owed_to_you = you_owe = ZERO
    for entry in (
        entries.filter(is_credit=True).annotate(settled=Coalesce(Sum("settlements__amount"), ZERO))
    ):
        left = max(entry.amount - entry.settled, ZERO)
        if entry.entry_type == LedgerEntry.EntryType.INCOME:
            owed_to_you += left
        else:
            you_owe += left
    lines = [
        translate(
            "wa.bk.summary", lang,
            month=today.strftime("%B %Y"),
            income=ksh(month["income"]),
            expenses=ksh(month["expenses"]),
            net=ksh(month["income"] - month["expenses"]),
            count=month["count"],
            owed_to_you=ksh(owed_to_you),
            you_owe=ksh(you_owe),
        )
    ]
    by_enterprise = (
        entries.filter(occurred_on__gte=start, occurred_on__lte=today)
        .values("enterprise__name")
        .annotate(
            income=Coalesce(Sum("amount", filter=Q(entry_type=LedgerEntry.EntryType.INCOME)), ZERO),
            expenses=Coalesce(Sum("amount", filter=Q(entry_type=LedgerEntry.EntryType.EXPENSE)), ZERO),
        )
        .order_by("enterprise__name")
    )
    if len(by_enterprise) > 1:
        lines.append(translate("wa.bk.by_business", lang))
        lines.extend(
            f"• {row['enterprise__name']}: {ksh(row['income'] - row['expenses'])}" for row in by_enterprise
        )
    return "\n".join(lines)


def recent_reply(user, lang):
    entries = (
        LedgerEntry.objects.filter(enterprise__owner=user, is_deleted=False)
        .select_related("enterprise")
        .annotate(settled=Coalesce(Sum("settlements__amount"), ZERO))
        .order_by("-occurred_on", "-created_at")[:5]
    )
    if not entries:
        return translate("wa.bk.no_entries", lang)
    lines = [translate("wa.bk.recent_title", lang)]
    for entry in entries:
        sign = "+" if entry.entry_type == LedgerEntry.EntryType.INCOME else "−"
        credit = ""
        if entry.is_credit and entry.amount - entry.settled > 0:
            credit = " " + translate("wa.bk.unpaid", lang, left=ksh(entry.amount - entry.settled))
        lines.append(
            f"{entry.occurred_on.strftime('%d %b')} {sign}{ksh(entry.amount)} — {entry.description}"
            f" ({entry.enterprise.name}){credit}"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------- entry points

def start_books(contact, lang):
    """Called once the contact is unlocked (or has no code yet)."""
    user = books_user(contact, create=False)
    if not _has_account(user):
        contact.flow, contact.step, contact.answers = "books", "consent", {}
        return translate("wa.bk.consent", lang)
    if not _enterprises(user):
        contact.flow, contact.step, contact.answers = "books", "ent_name", {"first": True}
        return translate("wa.bk.first_business", lang)
    return home(contact, lang)


def _ask_entry_business(contact, user, lang):
    enterprises = _enterprises(user)
    if len(enterprises) == 1:
        contact.answers["enterprise"] = enterprises[0].pk
        return _ask_category(contact, lang)
    contact.step = "pick_ent"
    return translate("wa.bk.which_business", lang, options=_numbered([e.name for e in enterprises], lang))


def _ask_category(contact, lang):
    contact.step = "category"
    labels = [translate(f"choice.ledger_category.{c}", lang) for c in _categories(contact.answers["kind"])]
    key = "wa.bk.ask_income_category" if contact.answers["kind"] == "income" else "wa.bk.ask_expense_category"
    return translate(key, lang, options=_numbered(labels, lang))


def _save_entry(contact, user, lang):
    answers = contact.answers
    enterprise = FarmEnterprise.objects.filter(pk=answers["enterprise"], owner=user).first()
    if enterprise is None:
        return home(contact, lang, translate("wa.bk.business_gone", lang))
    entry = LedgerEntry(
        enterprise=enterprise,
        entry_type=answers["kind"],
        category=answers["category"],
        amount=Decimal(answers["amount"]),
        occurred_on=date.fromisoformat(answers["date"]),
        description=answers["description"],
        counterparty=answers.get("counterparty", ""),
        is_credit=answers.get("credit", False),
    )
    entry.full_clean()
    entry.save()
    key = "wa.bk.saved_income" if entry.entry_type == LedgerEntry.EntryType.INCOME else "wa.bk.saved_expense"
    saved = translate(key, lang, amount=ksh(entry.amount), description=entry.description,
                      business=enterprise.name, day=entry.occurred_on.strftime("%d %b %Y"))
    if entry.is_credit:
        saved += "\n" + translate("wa.bk.saved_credit", lang)
    return home(contact, lang, saved)


def _save_settlement(contact, user, amount_text, lang):
    with transaction.atomic():
        entry = (
            LedgerEntry.objects.select_for_update()
            .filter(pk=contact.answers["credit_entry"], enterprise__owner=user, is_credit=True, is_deleted=False)
            .first()
        )
        if entry is None:
            return home(contact, lang, translate("wa.bk.credit_gone", lang))
        left = entry.amount - entry.settlements.aggregate(total=Coalesce(Sum("amount"), ZERO))["total"]
        amount = left if amount_text.strip().lower() in {"all", "yote"} else parse_amount(amount_text)
        if amount is None:
            return translate("wa.bk.invalid_amount", lang)
        if amount > left:
            return translate("wa.bk.overpayment", lang, left=ksh(left))
        CreditSettlement.objects.create(entry=entry, amount=amount, settled_on=timezone.localdate())
    remaining = left - amount
    key = "wa.bk.settled_full" if remaining <= 0 else "wa.bk.settled_part"
    return home(contact, lang, translate(key, lang, amount=ksh(amount), description=entry.description,
                                         left=ksh(remaining)))


def books_step(contact, text, lang):
    from .whatsapp import issue_code

    word = text.strip().lower()
    step = contact.step

    if step == "consent":
        if word not in YES_WORDS:
            return translate("wa.bk.consent_again", lang)
        user = books_user(contact, create=True)
        SmartHasibuAccount.objects.get_or_create(user=user, defaults={"consent_at": timezone.now()})
        prefix = ""
        if not contact.code_hash:
            prefix = translate("wa.bk.your_code", lang, code=issue_code(contact)) + "\n\n"
        contact.step, contact.answers = "ent_name", {"first": True}
        return prefix + translate("wa.bk.first_business", lang)

    # Every other step works on private records, so the unlock window must still be open.
    if not contact.unlocked_until or contact.unlocked_until <= timezone.now():
        contact.flow, contact.step, contact.answers = "unlock", "books", {}
        return translate("wa.ask_code", lang)
    user = books_user(contact, create=False)
    if not _has_account(user):
        return start_books(contact, lang)

    if step == "home":
        return _home_choice(contact, user, word, lang)

    if step == "ent_name":
        name = text.strip()
        if not 2 <= len(name) <= FarmEnterprise._meta.get_field("name").max_length:
            return translate("wa.bk.invalid_business_name", lang)
        if FarmEnterprise.objects.filter(owner=user, name__iexact=name).exists():
            return translate("wa.bk.business_exists", lang)
        contact.answers["name"] = name
        contact.step = "ent_cat"
        labels = [translate(f"choice.enterprise_category.{v}", lang) for v, _ in FarmEnterprise.Category.choices]
        return translate("wa.bk.ask_business_type", lang, options=_numbered(labels, lang))

    if step == "ent_cat":
        index = _pick(text, len(FarmEnterprise.Category.choices))
        if index is None:
            return translate("wa.fd.invalid_choice", lang)
        try:
            with transaction.atomic():
                enterprise = FarmEnterprise.objects.create(
                    owner=user, name=contact.answers["name"],
                    category=FarmEnterprise.Category.choices[index][0],
                )
        except IntegrityError:
            contact.step = "ent_name"
            return translate("wa.bk.business_exists", lang)
        return home(contact, lang, translate("wa.bk.business_added", lang, name=enterprise.name))

    if step == "pick_ent":
        enterprises = _enterprises(user)
        index = _pick(text, len(enterprises))
        if index is None:
            return translate("wa.fd.invalid_choice", lang)
        contact.answers["enterprise"] = enterprises[index].pk
        return _ask_category(contact, lang)

    if step == "category":
        categories = _categories(contact.answers["kind"])
        index = _pick(text, len(categories))
        if index is None:
            return translate("wa.fd.invalid_choice", lang)
        contact.answers["category"] = categories[index]
        contact.step = "amount"
        return translate("wa.bk.ask_amount", lang)

    if step == "amount":
        amount = parse_amount(text)
        if amount is None:
            return translate("wa.bk.invalid_amount", lang)
        contact.answers["amount"] = str(amount)
        contact.step = "description"
        return translate("wa.bk.ask_description", lang)

    if step == "description":
        description = text.strip()
        if not 2 <= len(description) <= LedgerEntry._meta.get_field("description").max_length:
            return translate("wa.bk.invalid_description", lang)
        contact.answers["description"] = description
        contact.step = "date"
        return translate("wa.bk.ask_date", lang)

    if step == "date":
        day = parse_date(text, timezone.localdate())
        if day is None:
            return translate("wa.bk.invalid_date", lang)
        contact.answers["date"] = day.isoformat()
        contact.step = "paid"
        key = "wa.bk.ask_paid_income" if contact.answers["kind"] == "income" else "wa.bk.ask_paid_expense"
        return translate(key, lang)

    if step == "paid":
        choice = _pick(text, 2)
        if choice is None:
            return translate("wa.fd.invalid_choice", lang)
        if choice == 0:
            return _save_entry(contact, user, lang)
        contact.answers["credit"] = True
        contact.step = "counterparty"
        key = "wa.bk.ask_customer" if contact.answers["kind"] == "income" else "wa.bk.ask_supplier"
        return translate(key, lang)

    if step == "counterparty":
        if word not in SKIP_WORDS:
            name = text.strip()
            if len(name) > LedgerEntry._meta.get_field("counterparty").max_length:
                return translate("wa.fd.too_long", lang, maximum=100)
            contact.answers["counterparty"] = name
        return _save_entry(contact, user, lang)

    if step == "pick_credit":
        entries = _open_credit(user)
        index = _pick(text, len(entries))
        if index is None:
            return translate("wa.fd.invalid_choice", lang)
        entry = entries[index]
        contact.answers["credit_entry"] = entry.pk
        contact.step = "settle_amount"
        return translate("wa.bk.ask_payment", lang, left=ksh(entry.amount - entry.settled))

    if step == "settle_amount":
        return _save_settlement(contact, user, text, lang)

    if step == "undo":
        if word in YES_WORDS:
            entry = LedgerEntry.objects.filter(
                pk=contact.answers.get("undo"), enterprise__owner=user, is_deleted=False
            ).first()
            if entry:
                entry.is_deleted, entry.deleted_at = True, timezone.now()
                entry.save(update_fields=["is_deleted", "deleted_at"])
                return home(contact, lang, translate("wa.bk.undone", lang, description=entry.description))
        return home(contact, lang, translate("wa.bk.kept", lang))

    return home(contact, lang)


def _home_choice(contact, user, word, lang):
    if word in {"1", "2"}:
        contact.answers = {"kind": "income" if word == "1" else "expense"}
        return _ask_entry_business(contact, user, lang)
    if word == "3":
        entries = _open_credit(user)
        if not entries:
            return home(contact, lang, translate("wa.bk.no_credit", lang))
        contact.step = "pick_credit"
        return translate("wa.bk.pick_credit", lang,
                         options=_numbered([_credit_label(e, lang) for e in entries], lang))
    if word == "4":
        return home(contact, lang, summary_reply(user, lang))
    if word == "5":
        return home(contact, lang, recent_reply(user, lang))
    if word == "6":
        entry = (
            LedgerEntry.objects.filter(enterprise__owner=user, is_deleted=False)
            .order_by("-created_at").first()
        )
        if entry is None:
            return home(contact, lang, translate("wa.bk.no_entries", lang))
        contact.step, contact.answers = "undo", {"undo": entry.pk}
        return translate("wa.bk.confirm_undo", lang, amount=ksh(entry.amount),
                         description=entry.description, day=entry.occurred_on.strftime("%d %b"))
    if word == "7":
        contact.step, contact.answers = "ent_name", {}
        names = ", ".join(e.name for e in _enterprises(user))
        return translate("wa.bk.add_business", lang, names=names)
    return translate("wa.bk.home", lang)
