#!/bin/sh
set -eu

if [ "${ANTIVIRUS_ENABLED:-False}" = "True" ] || [ "${ANTIVIRUS_ENABLED:-False}" = "true" ]; then
    mkdir -p "${PRIVATE_UPLOAD_ROOT:?PRIVATE_UPLOAD_ROOT must be configured}" /var/lib/clamav /var/log/clamav
    chown 10001:10001 "$PRIVATE_UPLOAD_ROOT" /var/lib/clamav /var/log/clamav
    gosu 10001:10001 freshclam --stdout --no-warnings
    gosu 10001:10001 freshclam --daemon --checks=12
fi

exec gosu 10001:10001 "$@"
