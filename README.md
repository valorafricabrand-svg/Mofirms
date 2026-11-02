# MoFirms

Marks Organic Farms Concepts Limited, trading as MoFirms, helps farmers, entrepreneurs, and organisations develop agricultural enterprises.

## Farmer, partner, and financial analysis backends

The website includes Django Portal A (farmer and farmer-group registration), Portal B (supplier, produce buyer, and service-provider registration), and Portal C (financial analysis requests). Portal C lets a customer request specialist-reviewed financial statements, business plans, cash-flow analysis, budgeting, or funding readiness. Staff scope the request, manage its status, and record a fee quote before work begins; there is no automated financial advice, audit, loan decision, payment collection, or public status lookup.

### Run locally on Windows

Use synthetic test information only. Local development uses SQLite, local file storage, an in-memory request limiter, and Django's development server; it is not configured for production or secure handling of real IDs.

```powershell
cd C:\path\to\mofirms
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py createsuperuser
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8002
```

Open the site at `http://127.0.0.1:8002/`, submit farmer registrations at `/portal/register/`, partner registrations at `/portal/partners/register/`, financial analysis requests at `/portal/financial-analysis/`, and review them at `/staff/`.

### Data and file safeguards

- Staff pages require a Django staff account. Evidence files are stored outside the static website, are not exposed through a public media URL, and are served only to authenticated staff as downloads.
- Accepted evidence is PDF/JPG/PNG only, maximum 5 MB each and 20 documents (100 MB total) per registration/request. Images are re-encoded to remove embedded metadata. Production uploads require ClamAV scanning.
- Government ID images, group registration evidence, farm evidence, partner business evidence, and financial-analysis records can be uploaded only with a separate document-consent checkbox. Registration alone does not mark a person, group, farm, business, or financial statement as verified.
- The selected schedules are deletion of documents 365 days after upload and deletion of farmer, partner, or financial-analysis requests after 730 days without recorded contact. Staff admin includes an action to update the last-contact date after an actual contact.
- Run `python manage.py purge_retained_data` to preview expired records. Run `python manage.py purge_retained_data --execute` to delete expired records and their private files. Schedule the execution command at least daily in production; protect backup copies with matching retention.
- The privacy notice, consent wording, lawful collection purpose, retention schedule, and identity-document handling must be reviewed and approved by MoFirms before real registrations open. Business-listing/referral consent is optional and does not create a public directory. Financial-analysis requests should collect approximate ranges only; do not collect personal ID numbers, tax PINs, bank credentials, passwords, or unrelated people's data through these forms.

### Production deployment checklist

Do not expose this service publicly until MoFirms has approved the data policy and configured a production environment:

1. Use PostgreSQL, HTTPS, a strong secret in `DJANGO_SECRET_KEY`, the exact production host in `DJANGO_ALLOWED_HOSTS`, and the matching origin in `DJANGO_CSRF_TRUSTED_ORIGINS`. If TLS terminates at a reverse proxy, set `DJANGO_TRUST_PROXY_SSL_HEADER=True` only when that trusted proxy strips and resets the forwarded-protocol header.
2. Set `DJANGO_DEBUG=False`, a shared Redis `REDIS_URL` for rate limits, and an encrypted private `PRIVATE_UPLOAD_ROOT` outside the code/repository directory. Keep database and file backups access-controlled and subject to the same retention schedule.
3. Run `python manage.py collectstatic` and configure the web server to publish only collected static files plus the site's public `/css/` and `/js/` assets. Never map `/private_uploads/` or `/private-media/` to a public URL.
4. Install ClamAV, keep its signatures current, set `ANTIVIRUS_ENABLED=True`, and configure `CLAMSCAN_COMMAND`. Configure a dedicated staff account for each reviewer; do not share administrator credentials.
5. Configure logging, monitoring, restore-tested backups, and a daily retention purge. Review access controls and consent/retention wording before inviting farmers.

The public website remains available as static files, but Portals A, B, and C submissions and staff review require the Django application. See `.env.example` for environment variable names.

## Website notes

- Edit service statuses and website copy in `js/app.js` and `index.html`.
- The existing general enquiry form opens the visitor's email app; it does not persist enquiries.
- Confirm contact details, logo, domain, privacy wording, and company sign-off before launch.
