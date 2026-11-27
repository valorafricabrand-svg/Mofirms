import json
import logging
import time
import urllib.error
import urllib.request

from django.conf import settings

logger = logging.getLogger(__name__)


class GeminiUnavailable(Exception):
    pass


def generate(contents, system_prompt, *, max_output_tokens=400, temperature=0.4, timeout=15):
    """Call Gemini with retries and fallback models; return the reply text."""
    if not settings.GEMINI_API_KEY:
        raise GeminiUnavailable("GEMINI_API_KEY is not configured.")
    body = json.dumps(
        {
            "contents": contents,
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "generationConfig": {
                "maxOutputTokens": max_output_tokens,
                "temperature": temperature,
                "thinkingConfig": {"thinkingBudget": 0},
            },
        }
    ).encode("utf-8")
    models_to_try = [settings.GEMINI_MODEL] + [
        model for model in settings.GEMINI_FALLBACK_MODELS if model != settings.GEMINI_MODEL
    ]
    started = time.monotonic()
    for model_index, model in enumerate(models_to_try):
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model}:generateContent?key={settings.GEMINI_API_KEY}"
        )
        attempts = 2 if model_index == 0 else 1
        for attempt in range(1, attempts + 1):
            request = urllib.request.Request(
                url, data=body, headers={"Content-Type": "application/json"}, method="POST"
            )
            try:
                with urllib.request.urlopen(request, timeout=timeout) as response:
                    data = json.loads(response.read().decode("utf-8"))
            except (urllib.error.URLError, TimeoutError) as exc:
                detail = exc.read().decode("utf-8", "ignore")[:500] if isinstance(exc, urllib.error.HTTPError) else str(exc)
                logger.warning(
                    "Gemini request failed on model %s attempt %d after %.1fs (%s): %s",
                    model, attempt, time.monotonic() - started, type(exc).__name__, detail,
                )
                retryable = not isinstance(exc, urllib.error.HTTPError) or exc.code in (429, 503)
                if attempt < attempts and retryable:
                    time.sleep(attempt)
                    continue
                break
            try:
                return data["candidates"][0]["content"]["parts"][0]["text"]
            except (KeyError, IndexError, TypeError):
                logger.warning("Gemini returned no usable candidate: %s", data)
                break
    raise GeminiUnavailable("No Gemini model returned a usable reply.")
