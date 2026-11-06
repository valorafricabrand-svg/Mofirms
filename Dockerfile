FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends clamav clamav-freshclam gosu \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --system --uid 10001 --user-group --no-create-home --shell /usr/sbin/nologin mofirms \
    && sed -i 's/^#\?DatabaseOwner .*/DatabaseOwner mofirms/' /etc/clamav/freshclam.conf \
    && mkdir -p /var/data/private_uploads /var/lib/clamav /var/log/clamav \
    && chown -R 10001:10001 /var/data /var/lib/clamav /var/log/clamav

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN python manage.py collectstatic --no-input \
    && chmod +x /app/scripts/container-entrypoint.sh

EXPOSE 10000
ENTRYPOINT ["/app/scripts/container-entrypoint.sh"]
CMD ["gunicorn", "mofirms_backend.wsgi:application", "--bind", "0.0.0.0:10000", "--workers", "1", "--timeout", "60", "--access-logfile", "-", "--error-logfile", "-"]
