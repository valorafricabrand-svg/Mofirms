import logging
import uuid

from django.core.cache import cache
from django.db import DatabaseError, connection
from django.http import HttpResponse
from django.views.decorators.http import require_GET
from redis.exceptions import RedisError


logger = logging.getLogger(__name__)


@require_GET
def health_check(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        key = f"health-check:{uuid.uuid4()}"
        cache.set(key, "ok", timeout=5)
        if cache.get(key) != "ok":
            raise RedisError("Cache health check did not return the written value.")
        cache.delete(key)
    except (DatabaseError, OSError, RedisError):
        logger.exception("Production health check failed.")
        return HttpResponse("Service unavailable", status=503)
    return HttpResponse("OK")
