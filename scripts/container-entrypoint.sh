#!/bin/sh
set -eu

if [ "${ANTIVIRUS_ENABLED:-False}" = "True" ] || [ "${ANTIVIRUS_ENABLED:-False}" = "true" ]; then
    mkdir -p "${PRIVATE_UPLOAD_ROOT:?PRIVATE_UPLOAD_ROOT must be configured}" /var/lib/clamav /var/log/clamav
    chown 10001:10001 "$PRIVATE_UPLOAD_ROOT" /var/lib/clamav /var/log/clamav
    # Signature download can be rate-limited from cloud IPs. Never let that stop the
    # web server: uploads fail closed until signatures exist, and the daemon retries.
    attempt=1
    until gosu 10001:10001 freshclam --stdout --no-warnings; do
        if [ "$attempt" -ge 3 ]; then
            echo "WARNING: freshclam could not download signatures; uploads will be rejected until the background updater succeeds." >&2
            break
        fi
        attempt=$((attempt + 1))
        sleep 10
    done
    gosu 10001:10001 freshclam --daemon --checks=12 || echo "WARNING: freshclam daemon failed to start." >&2
fi

exec gosu 10001:10001 "$@"
