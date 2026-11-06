import hashlib
import hmac
import os
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from urllib.parse import urlparse


_SUCCESS_RESPONSE = b"Retention purge completed."


def send_retention_purge(endpoint, secret, opener=None):
    if not endpoint:
        raise ValueError("RETENTION_WEBHOOK_URL must be an absolute HTTPS URL.")
    parsed_endpoint = urlparse(endpoint)
    if not secret or len(secret) < 32:
        raise ValueError(
            "A generated RETENTION_WEBHOOK_SECRET of at least 32 characters is required."
        )
    if parsed_endpoint.scheme != "https" or not parsed_endpoint.netloc:
        raise ValueError("RETENTION_WEBHOOK_URL must be an absolute HTTPS URL.")

    timestamp = str(int(time.time()))
    signature = hmac.new(
        secret.encode("utf-8"),
        timestamp.encode("ascii") + b".",
        hashlib.sha256,
    ).hexdigest()
    request = Request(
        endpoint,
        data=b"",
        headers={
            "X-MoFirms-Timestamp": timestamp,
            "X-MoFirms-Signature": signature,
        },
        method="POST",
    )
    open_url = opener if opener is not None else urlopen
    try:
        with open_url(request, timeout=60) as response:
            body = response.read(1024)
            if response.status != 200:
                raise RuntimeError(f"Retention endpoint returned HTTP {response.status}.")
    except HTTPError as error:
        raise RuntimeError(f"Retention endpoint returned HTTP {error.code}.") from error
    except (OSError, URLError, TimeoutError) as error:
        raise RuntimeError("Could not reach the retention endpoint.") from error

    if body != _SUCCESS_RESPONSE:
        raise RuntimeError("Retention endpoint returned an unexpected response.")


def main():
    endpoint = os.environ.get("RETENTION_WEBHOOK_URL", "")
    secret = os.environ.get("RETENTION_WEBHOOK_SECRET", "")
    try:
        send_retention_purge(endpoint, secret)
    except (RuntimeError, ValueError) as error:
        raise SystemExit(str(error)) from error
    print("Production retention purge completed.")


if __name__ == "__main__":
    main()
