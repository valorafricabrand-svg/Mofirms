import hashlib
import hmac
import logging
import time
from io import StringIO

from django.conf import settings
from django.core.management import call_command
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST


logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def run_retention_purge(request):
    secret = settings.RETENTION_WEBHOOK_SECRET
    timestamp = request.headers.get("X-MoFirms-Timestamp", "")
    signature = request.headers.get("X-MoFirms-Signature", "")
    if not secret or not timestamp.isdecimal() or len(request.body) != 0:
        return HttpResponse(status=403)
    if abs(int(time.time()) - int(timestamp)) > 300:
        return HttpResponse(status=403)

    message = timestamp.encode("ascii") + b"."
    expected_signature = hmac.new(
        secret.encode("utf-8"), message, hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(signature, expected_signature):
        return HttpResponse(status=403)

    output = StringIO()
    call_command("purge_retained_data", execute=True, stdout=output)
    result = output.getvalue().strip()
    logger.info("Scheduled retention purge completed: %s", result)
    return HttpResponse("Retention purge completed.")
