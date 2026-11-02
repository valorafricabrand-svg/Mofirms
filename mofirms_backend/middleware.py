from django.conf import settings
from django.http import HttpResponseNotAllowed


class DemoReadOnlyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if settings.DEMO_MODE and request.method not in {"GET", "HEAD", "OPTIONS"}:
            return HttpResponseNotAllowed(
                ["GET", "HEAD", "OPTIONS"],
                "This public demo is read-only. Form submissions and uploads are disabled.",
            )
        return self.get_response(request)
