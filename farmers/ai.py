"""Claude (Anthropic) text generation for the website assistant and newsletter drafts.

One entry point, `generate`, so every AI feature on the site shares the same model,
error handling and logging. Callers pass plain role/text turns; this module turns them
into a Messages API request.
"""

import logging
from functools import lru_cache

import anthropic
from django.conf import settings

logger = logging.getLogger(__name__)

# If Claude declines a request on safety grounds, the API re-runs it on a fallback
# model inside the same call instead of failing outright.
FALLBACK_BETA = "server-side-fallback-2026-07-01"


class AIUnavailable(Exception):
    """The AI could not produce a reply (not configured, network, quota, outage)."""


class AIRefused(AIUnavailable):
    """Claude declined to answer this request."""


def configured():
    return bool(settings.ANTHROPIC_API_KEY)


@lru_cache(maxsize=1)
def _client(api_key):
    return anthropic.Anthropic(api_key=api_key)


def _turns(conversation):
    """Accept [{"role": "user"|"assistant", "text": str}] and return API messages.

    The API needs the first message to be from the user, so any leading assistant
    turns (e.g. a greeting from the chat widget) are dropped.
    """
    messages = [
        {"role": turn["role"], "content": turn["text"]}
        for turn in conversation
        if turn.get("role") in ("user", "assistant") and (turn.get("text") or "").strip()
    ]
    while messages and messages[0]["role"] != "user":
        messages.pop(0)
    return messages


def generate(conversation, system_prompt, *, effort="low", max_tokens=16000, timeout=25):
    """Return Claude's reply text for a short conversation, or raise AIUnavailable."""
    if not configured():
        raise AIUnavailable("ANTHROPIC_API_KEY is not configured.")
    messages = _turns(conversation)
    if not messages:
        raise AIUnavailable("There is no user message to answer.")

    client = _client(settings.ANTHROPIC_API_KEY).with_options(timeout=timeout, max_retries=1)
    try:
        response = client.beta.messages.create(
            model=settings.ANTHROPIC_MODEL,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=messages,
            output_config={"effort": effort},
            betas=[FALLBACK_BETA],
            fallbacks="default",
        )
    except (anthropic.AuthenticationError, anthropic.PermissionDeniedError) as exc:
        logger.error("Claude rejected the API key or its permissions: %s", exc)
        raise AIUnavailable("Claude API key problem.") from exc
    except anthropic.RateLimitError as exc:
        logger.warning("Claude rate limit reached: %s", exc)
        raise AIUnavailable("Claude is rate limited.") from exc
    except anthropic.APIStatusError as exc:
        logger.warning("Claude returned HTTP %s (request %s): %s",
                       exc.status_code, exc.response.headers.get("request-id"), exc)
        raise AIUnavailable("Claude returned an error.") from exc
    except anthropic.APIConnectionError as exc:  # includes timeouts
        logger.warning("Could not reach Claude: %s", exc)
        raise AIUnavailable("Could not reach Claude.") from exc

    if response.stop_reason == "refusal":
        category = getattr(response.stop_details, "category", None) if response.stop_details else None
        logger.info("Claude declined a request (category %s, request %s).", category, response._request_id)
        raise AIRefused("Claude declined this request.")

    text = "".join(block.text for block in response.content if block.type == "text").strip()
    if not text:
        logger.warning("Claude returned no text (stop reason %s, request %s).",
                       response.stop_reason, response._request_id)
        raise AIUnavailable("Claude returned an empty reply.")
    if response.stop_reason == "max_tokens":
        logger.warning("Claude reply was cut off at max_tokens (request %s).", response._request_id)
    return text
