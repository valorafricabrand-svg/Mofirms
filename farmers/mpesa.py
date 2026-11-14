import base64
import json
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from django.conf import settings
from django.utils import timezone


class MpesaError(Exception):
    pass


def payments_available():
    if not settings.MPESA_ENABLED:
        return False
    return all(
        (
            settings.MPESA_CONSUMER_KEY,
            settings.MPESA_CONSUMER_SECRET,
            settings.MPESA_SHORTCODE,
            settings.MPESA_PASSKEY,
            settings.MPESA_CALLBACK_URL,
        )
    )


def mask_phone_number(phone_number):
    return f"ending {phone_number[-4:]}"


def normalize_phone_number(phone_number):
    digits = re.sub(r"\D", "", phone_number)
    if digits.startswith("0") and len(digits) == 10:
        digits = f"254{digits[1:]}"
    elif digits.startswith("7") and len(digits) == 9:
        digits = f"254{digits}"
    elif digits.startswith("1") and len(digits) == 9:
        digits = f"254{digits}"
    if not re.fullmatch(r"254(?:7|1)\d{8}", digits):
        raise MpesaError("Enter a valid Kenyan mobile number, for example 0712345678.")
    return digits


def _credentials():
    if not settings.MPESA_ENABLED:
        raise MpesaError(
            "M-PESA checkout is not enabled yet. Contact MoFirms to confirm when payment setup is complete."
        )
    required = {
        "MPESA_CONSUMER_KEY": settings.MPESA_CONSUMER_KEY,
        "MPESA_CONSUMER_SECRET": settings.MPESA_CONSUMER_SECRET,
        "MPESA_SHORTCODE": settings.MPESA_SHORTCODE,
        "MPESA_PASSKEY": settings.MPESA_PASSKEY,
        "MPESA_CALLBACK_URL": settings.MPESA_CALLBACK_URL,
    }
    missing = [key for key, value in required.items() if not value]
    if missing:
        raise MpesaError(
            "M-PESA payment is not configured. Ask MoFirms to complete the secure payment setup."
        )
    callback = urlparse(settings.MPESA_CALLBACK_URL)
    if not callback.scheme or not callback.netloc:
        raise MpesaError("The M-PESA callback URL is invalid.")
    if not settings.DEBUG and callback.scheme != "https":
        raise MpesaError("The M-PESA callback URL must use HTTPS.")
    return required


def _request_json(url, *, headers=None, data=None, method=None):
    request = Request(url, data=data, headers=headers or {}, method=method)
    try:
        with urlopen(request, timeout=15) as response:
            response_body = response.read()
    except HTTPError as error:
        raise MpesaError(f"M-PESA returned HTTP {error.code}.") from error
    except (OSError, URLError, TimeoutError) as error:
        raise MpesaError("M-PESA could not be reached. Please try again shortly.") from error

    try:
        payload = json.loads(response_body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise MpesaError("M-PESA returned an unreadable response.") from error
    if not isinstance(payload, dict):
        raise MpesaError("M-PESA returned an unexpected response.")
    return payload


def _access_token(credentials):
    url = f"{settings.MPESA_BASE_URL}/oauth/v1/generate?grant_type=client_credentials"
    auth_value = base64.b64encode(
        f"{credentials['MPESA_CONSUMER_KEY']}:{credentials['MPESA_CONSUMER_SECRET']}".encode()
    ).decode("ascii")
    response = _request_json(
        url,
        headers={"Authorization": f"Basic {auth_value}"},
    )
    token = response.get("access_token")
    if not isinstance(token, str) or not token:
        raise MpesaError("M-PESA authentication failed.")
    return token


def _password_and_timestamp(credentials):
    timestamp = timezone.localtime().strftime("%Y%m%d%H%M%S")
    value = (
        f"{credentials['MPESA_SHORTCODE']}"
        f"{credentials['MPESA_PASSKEY']}{timestamp}"
    )
    password = base64.b64encode(value.encode()).decode("ascii")
    return password, timestamp


def initiate_stk_push(*, phone_number, amount, account_reference, description):
    credentials = _credentials()
    phone = normalize_phone_number(phone_number)
    if amount <= 0 or int(amount) != amount:
        raise MpesaError("M-PESA payments must be a positive whole number of Kenyan shillings.")
    password, timestamp = _password_and_timestamp(credentials)
    payload = {
        "BusinessShortCode": credentials["MPESA_SHORTCODE"],
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": settings.MPESA_TRANSACTION_TYPE,
        "Amount": int(amount),
        "PartyA": phone,
        "PartyB": credentials["MPESA_SHORTCODE"],
        "PhoneNumber": phone,
        "CallBackURL": settings.MPESA_CALLBACK_URL,
        "AccountReference": account_reference[:12],
        "TransactionDesc": description[:13],
    }
    response = _request_json(
        f"{settings.MPESA_BASE_URL}/mpesa/stkpush/v1/processrequest",
        headers={
            "Authorization": f"Bearer {_access_token(credentials)}",
            "Content-Type": "application/json",
        },
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
    )
    if response.get("ResponseCode") != "0":
        message = response.get("errorMessage") or response.get("ResponseDescription")
        raise MpesaError(str(message or "M-PESA could not start the payment request."))
    checkout_request_id = response.get("CheckoutRequestID")
    merchant_request_id = response.get("MerchantRequestID")
    if not checkout_request_id or not merchant_request_id:
        raise MpesaError("M-PESA did not return the payment request identifiers.")
    return {
        "checkout_request_id": str(checkout_request_id),
        "merchant_request_id": str(merchant_request_id),
        "customer_message": str(response.get("CustomerMessage", ""))[:255],
    }


def query_stk_status(checkout_request_id):
    credentials = _credentials()
    password, timestamp = _password_and_timestamp(credentials)
    payload = {
        "BusinessShortCode": credentials["MPESA_SHORTCODE"],
        "Password": password,
        "Timestamp": timestamp,
        "CheckoutRequestID": checkout_request_id,
    }
    response = _request_json(
        f"{settings.MPESA_BASE_URL}/mpesa/stkpushquery/v1/query",
        headers={
            "Authorization": f"Bearer {_access_token(credentials)}",
            "Content-Type": "application/json",
        },
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
    )
    if response.get("ResponseCode") != "0":
        raise MpesaError("M-PESA could not confirm the payment status.")
    return response
