"""Claude answers free-text questions on WhatsApp.

Only questions that aren't a menu choice reach Claude: numbers, login codes, menu words
and the step-by-step forms keep working exactly as before. The answer is produced in a
background thread so the webhook replies to Meta straight away.

Recent turns are kept in the cache (not the database) for 30 minutes so follow-up
questions make sense, then they expire on their own.
"""

import logging
import re
import threading

from django.conf import settings
from django.core.cache import cache

from . import ai
from .templatetags.custom_i18n import translate

logger = logging.getLogger(__name__)

AI_ANSWERS_PER_DAY = 15
GLOBAL_PER_MINUTE = 30
HISTORY_SECONDS = 30 * 60
HISTORY_TURNS = 6
MAX_QUESTION_LENGTH = 1000

SYSTEM_PROMPT = (
    "You are the MoFirms WhatsApp assistant. MoFirms (Marks Organic Farms Concepts Limited) "
    "helps farmers, entrepreneurs and organisations in Kenya plan agricultural businesses, "
    "assess opportunities and grow sustainably through financial analysis, market "
    "development, training and digital tools such as SmartHasibu farm records.\n\n"
    "Answer questions about farming, agribusiness and MoFirms' services helpfully and "
    "briefly, for small-scale farmers reading on a phone. Keep replies under about 120 "
    "words. Reply in {language}, or in the language the person writes in if it is "
    "different.\n\n"
    "This chat also has a numbered menu. When a service fits what the person wants, tell "
    "them which number to send:\n"
    "1 - register as a farmer or farmer group\n"
    "2 - register as a supplier, buyer or service provider\n"
    "3 - request financial analysis or a business plan\n"
    "4 - request a risk and opportunity assessment\n"
    "5 - apply as a researcher\n"
    "6 - check registration status, 7 - see their dashboard\n"
    "9 - ask the MoFirms team to call them back\n"
    "10 - request a consultation\n"
    "11 - SmartHasibu: record sales and costs\n\n"
    "Rules:\n"
    "- Never ask for or repeat ID numbers, KRA PINs, M-PESA PINs, passwords, login codes or "
    "bank details. If someone shares one, tell them not to share it in chat.\n"
    "- You cannot see their registration, records or requests, and you cannot make "
    "bookings, payments or promises on MoFirms' behalf. For anything about their own "
    "account, prices, quotes or legal, medical or veterinary emergencies, point them to the "
    "right menu number or to 9 for a call back.\n"
    "- If you are not sure of a local fact (prices, dates, regulations), say so rather "
    "than guessing.\n"
    "- WhatsApp formatting only: plain sentences, *single asterisks* for bold if needed, "
    "short lists with '-' . No Markdown headings, tables or links you were not given."
)

LANGUAGE_NAMES = {"en": "English", "sw": "Kiswahili"}


class PendingAIAnswer:
    """Returned by the bot instead of a reply: the webhook answers it in the background."""

    def __init__(self, phone, text, lang):
        self.phone, self.text, self.lang = phone, text, lang


def is_question(text):
    """Free text worth sending to Claude: has letters and isn't just a code or number."""
    text = text.strip()
    return (
        ai.configured()
        and 3 <= len(text) <= MAX_QUESTION_LENGTH
        and re.search(r"[^\W\d_]", text) is not None
    )


def _within_limits(phone):
    per_phone = f"wa:ai:count:{phone}"
    if cache.add(per_phone, 1, 24 * 60 * 60):
        phone_count = 1
    else:
        try:
            phone_count = cache.incr(per_phone)
        except ValueError:
            phone_count = 1
    if phone_count > AI_ANSWERS_PER_DAY:
        return "daily"
    if not cache.add("wa:ai:global-rpm", 1, 60):
        try:
            if cache.incr("wa:ai:global-rpm") > GLOBAL_PER_MINUTE:
                return "busy"
        except ValueError:
            pass
    return None


def answer(pending):
    """Produce the reply text for a PendingAIAnswer (runs in the background)."""
    lang = pending.lang
    limit = _within_limits(pending.phone)
    if limit == "daily":
        return translate("wa.ai_daily_limit", lang)
    if limit == "busy":
        return translate("wa.ai_unavailable", lang)

    history_key = f"wa:ai:history:{pending.phone}"
    history = cache.get(history_key) or []
    conversation = history + [{"role": "user", "text": pending.text}]
    system = SYSTEM_PROMPT.format(language=LANGUAGE_NAMES.get(lang, "English"))
    try:
        reply = ai.generate(conversation, system, effort="low", timeout=40)
    except ai.AIRefused:
        return translate("wa.ai_refused", lang)
    except ai.AIUnavailable:
        return translate("wa.ai_unavailable", lang)
    cache.set(
        history_key,
        (conversation + [{"role": "assistant", "text": reply}])[-HISTORY_TURNS:],
        HISTORY_SECONDS,
    )
    return reply + "\n\n" + translate("wa.ai_footer", lang)


def send_answer(pending):
    from .whatsapp import send_text

    try:
        reply = answer(pending)
    except Exception:
        logger.exception("Could not produce a WhatsApp AI answer.")
        reply = translate("wa.ai_unavailable", pending.lang)
    send_text(pending.phone, reply)


def dispatch(pending):
    if settings.WHATSAPP_AI_ASYNC:
        threading.Thread(target=send_answer, args=(pending,), daemon=True).start()
    else:
        send_answer(pending)
