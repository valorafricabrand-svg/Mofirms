from urllib.parse import urlparse

from django.http import HttpResponseRedirect
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_GET

LANGUAGE_COOKIE_NAME = "lang"
LANGUAGE_COOKIE_MAX_AGE = 60 * 60 * 24 * 365


@require_GET
def set_language(request):
    code = request.GET.get("lang", "en")
    code = "sw" if code == "sw" else "en"

    next_url = request.GET.get("next") or request.META.get("HTTP_REFERER") or "/"
    parsed = urlparse(next_url)
    if parsed.netloc and not url_has_allowed_host_and_scheme(
        next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        next_url = "/"

    response = HttpResponseRedirect(next_url)
    response.set_cookie(
        LANGUAGE_COOKIE_NAME,
        code,
        max_age=LANGUAGE_COOKIE_MAX_AGE,
        samesite="Lax",
    )
    return response
