"""Sign in to SmartHasibu with a Google account (OpenID Connect code flow).

Flow: google_start -> Google consent screen -> google_callback. Returning users
are signed straight in. New users (or existing site users without a cashbook)
see google_confirm to give consent before an account is created.
"""

import base64
import json
import logging
import secrets
import time
import urllib.error
import urllib.parse
import urllib.request

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.db import IntegrityError, transaction
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_http_methods

from farmers.templatetags.custom_i18n import current_lang, translate
from .models import SmartHasibuAccount


logger = logging.getLogger(__name__)

AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_ISSUERS = {"accounts.google.com", "https://accounts.google.com"}
SESSION_STATE = "sh_google_state"
SESSION_PENDING = "sh_google_pending"
PENDING_MAX_AGE = 10 * 60
MODEL_BACKEND = "django.contrib.auth.backends.ModelBackend"


def google_enabled():
    return bool(settings.GOOGLE_OAUTH_CLIENT_ID and settings.GOOGLE_OAUTH_CLIENT_SECRET)


def _redirect_uri(request):
    if settings.GOOGLE_OAUTH_REDIRECT_URI:
        return settings.GOOGLE_OAUTH_REDIRECT_URI
    uri = request.build_absolute_uri(reverse("smart_hasibu:google_callback"))
    if not settings.DEBUG and uri.startswith("http://"):
        uri = "https://" + uri[len("http://"):]
    return uri


def _fail(request, key="sh.google.failed"):
    messages.error(request, translate(key, current_lang(request)))
    return redirect("smart_hasibu:login")


def _exchange_code(code, redirect_uri):
    body = urllib.parse.urlencode(
        {
            "code": code,
            "client_id": settings.GOOGLE_OAUTH_CLIENT_ID,
            "client_secret": settings.GOOGLE_OAUTH_CLIENT_SECRET,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }
    ).encode()
    request = urllib.request.Request(
        TOKEN_URL,
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.loads(response.read().decode())


def _id_token_claims(id_token):
    # The token came straight from Google's token endpoint over TLS, so per
    # OpenID Connect Core 3.1.3.7 its signature does not need re-checking here.
    # The claims themselves are still validated by the caller.
    parts = id_token.split(".")
    if len(parts) != 3:
        raise ValueError("malformed id_token")
    payload = parts[1] + "=" * (-len(parts[1]) % 4)
    return json.loads(base64.urlsafe_b64decode(payload.encode()))


def _valid_claims(claims, nonce):
    return (
        claims.get("iss") in GOOGLE_ISSUERS
        and claims.get("aud") == settings.GOOGLE_OAUTH_CLIENT_ID
        and int(claims.get("exp", 0)) > time.time()
        and secrets.compare_digest(str(claims.get("nonce", "")), nonce)
        and claims.get("email_verified") is True
        and bool(claims.get("email"))
    )


@require_GET
def google_start(request):
    if not google_enabled():
        return _fail(request, "sh.google.unavailable")
    state = secrets.token_urlsafe(24)
    nonce = secrets.token_urlsafe(24)
    request.session[SESSION_STATE] = {"state": state, "nonce": nonce}
    params = {
        "client_id": settings.GOOGLE_OAUTH_CLIENT_ID,
        "redirect_uri": _redirect_uri(request),
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "nonce": nonce,
        "prompt": "select_account",
    }
    return redirect(f"{AUTHORIZE_URL}?{urllib.parse.urlencode(params)}")


@require_GET
def google_callback(request):
    saved = request.session.pop(SESSION_STATE, None)
    state = request.GET.get("state", "")
    if not saved or not state or not secrets.compare_digest(state, saved["state"]):
        return _fail(request)
    if request.GET.get("error"):
        # The person pressed Cancel on Google's screen.
        return redirect("smart_hasibu:login")
    code = request.GET.get("code")
    if not code or not google_enabled():
        return _fail(request)

    try:
        tokens = _exchange_code(code, _redirect_uri(request))
        claims = _id_token_claims(tokens["id_token"])
    except (urllib.error.URLError, TimeoutError, KeyError, ValueError) as error:
        logger.warning("Google sign-in token exchange failed: %s", error)
        return _fail(request)
    if not _valid_claims(claims, saved["nonce"]):
        logger.warning("Google sign-in rejected an id_token with invalid claims.")
        return _fail(request)

    email = claims["email"].strip().lower()
    user = get_user_model().objects.filter(email__iexact=email).first()
    if user is not None:
        if user.is_staff or user.is_superuser:
            # Staff accounts can open the admin, so keep them on password sign-in.
            return _fail(request, "sh.google.staff_blocked")
        if not user.is_active:
            return _fail(request)
        if SmartHasibuAccount.objects.filter(user=user).exists():
            login(request, user, backend=MODEL_BACKEND)
            return redirect("smart_hasibu:dashboard")

    request.session[SESSION_PENDING] = {
        "email": email,
        "name": (claims.get("name") or claims.get("given_name") or "").strip()[:150],
        "at": time.time(),
    }
    return redirect("smart_hasibu:google_confirm")


@require_http_methods(["GET", "POST"])
def google_confirm(request):
    pending = request.session.get(SESSION_PENDING)
    if not pending or time.time() - pending.get("at", 0) > PENDING_MAX_AGE:
        request.session.pop(SESSION_PENDING, None)
        return redirect("smart_hasibu:login")

    lang = current_lang(request)
    error = None
    if request.method == "POST":
        if request.POST.get("consent") != "on":
            error = translate("sh.google.consent_required", lang)
        else:
            user = _create_account(pending)
            if user is None:
                return _fail(request)
            request.session.pop(SESSION_PENDING, None)
            login(request, user, backend=MODEL_BACKEND)
            return redirect("smart_hasibu:dashboard")

    return render(
        request,
        "smart_hasibu/google_confirm.html",
        {"email": pending["email"], "name": pending["name"], "error": error},
    )


def _create_account(pending):
    user_model = get_user_model()
    email = pending["email"]
    try:
        with transaction.atomic():
            user = user_model.objects.filter(email__iexact=email).first()
            if user is None:
                user = user_model(username=email, email=email, first_name=pending["name"])
                user.set_unusable_password()
                user.save()
            elif user.is_staff or user.is_superuser or not user.is_active:
                return None
            SmartHasibuAccount.objects.get_or_create(
                user=user, defaults={"consent_at": timezone.now()}
            )
    except IntegrityError:
        logger.exception("Could not create a SmartHasibu account from Google sign-in.")
        return None
    return user
