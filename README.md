# MoFirms

Marks Organic Farms Concepts Limited, trading as MoFirms, helps farmers, entrepreneurs, and organisations develop agricultural enterprises.

## Farmer, partner, finance, and research portals

The website includes Django Portal A (farmer and farmer-group registration), Portal B (supplier, produce buyer, and service-provider registration), Portal C (financial analysis requests), Portal D (risk and opportunity assessment requests), and Portal E (independent research registration and questionnaires). Portal C lets a customer request specialist-reviewed financial statements, business plans, cash-flow analysis, budgeting, or funding readiness. Portal D accepts a scoped request for human-led enterprise risk, resilience, and opportunity assessment. For both portals, staff review the request, manage its status, and record a fee quote before work begins; there is no automated financial or risk scoring, audit, loan or investment decision, payment collection, or public status lookup.

SmartHasibu is a separate, account-protected Django bookkeeping pilot. A farmer can create private enterprise books, record income and expenses, mark credit, record partial repayments, and view monthly totals and unpaid balances. A pilot account can access only its own records. SmartHasibu does not process payments, synchronize offline entries, share group books, or provide audited accounts. Use synthetic information only until production infrastructure and farmer data protections are approved.

Portal E is independent of farmer/partner onboarding. Researchers and students apply with an account that remains disabled until manual MoFirms vetting. Each study is separately reviewed for purpose, methods, ethics, target group, fee, questionnaire, and respondent consent; staff must approve and publish a study before creating invitations. Staff can invite only customer contacts who gave separate permission to receive research invitations. Respondents then make a separate, voluntary choice for each study. Researcher dashboards show aggregate counts only once at least five responses exist; any question with a non-zero answer category smaller than five is withheld. Questionnaires use fixed-choice questions and do not collect free-text answers, names, email, phone, or respondent profile fields. Completed invitations are disconnected from their farmer/partner profile; researchers cannot see invitation lists, contact details, or individual answers.

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

Open the site at `http://127.0.0.1:8002/`, submit farmer registrations at `/portal/register/`, partner registrations at `/portal/partners/register/`, financial analysis requests at `/portal/financial-analysis/`, risk and opportunity assessment requests at `/portal/risk-assessment/`, SmartHasibu at `/smart-hasibu/`, researcher applications at `/portal/research/register/`, researcher sign-in at `/portal/research/login/`, and staff review at `/staff/`.

### Private beta, service plans, and M-PESA

The public pricing page (`/pricing/`) reads active packages from the `ServicePlan` table. Migration `0008` creates the initial Farm Starter (KSh 4,500), Growth (KSh 12,500), and Enterprise Accelerator (KSh 29,000) packages. These are proposed launch prices; confirm the fees, deliverables, taxes, and refund/cancellation terms before accepting live payments. Staff can edit or deactivate packages in Django admin.

The private beta flow is deliberately staff-gated:

1. Review the farmer or entrepreneur in the Farmer registrations or Supplier and buyer registrations admin. Set verification to Verified only after recording the evidence and scope in verification notes.
2. Create a Beta invite for the verified profile in Django admin. Send its private link directly through an authorised channel; there is no automated email or SMS integration. Invites expire after 30 days and can be revoked.
3. The invited person consents and submits a beta access request. Staff review the resulting Beta enrollment and set its status to Approved or Declined.
4. Share the access link with an approved member. They select an active package and a Kenyan M-PESA number; the server starts an STK Push using the package price stored in the database.
5. MoFirms marks the payment paid only after the Daraja callback is matched to the stored checkout request and confirmed using the STK Query API. Review the resulting payment record in Django admin before beginning paid work.

Configure these server environment variables through the hosting provider's secret manager. Never commit or send credentials in source control, support tickets, or chat:

- `MPESA_ENVIRONMENT=sandbox` for test credentials; use `production` only after Safaricom merchant onboarding and test approval.
- `MPESA_CONSUMER_KEY`, `MPESA_CONSUMER_SECRET`, `MPESA_SHORTCODE`, and `MPESA_PASSKEY` from the matching Daraja app and shortcode.
- `MPESA_CALLBACK_URL=https://<production-host>/portal/payments/mpesa/callback/` using the exact public HTTPS address.
- `MPESA_TRANSACTION_TYPE=CustomerPayBillOnline` for a PayBill shortcode, or `CustomerBuyGoodsOnline` for a Till where enabled.

The callback must be reachable over HTTPS in production. Keep the configured environment and merchant credentials paired (sandbox credentials with sandbox, live credentials with production). The site does not store M-PESA PINs or card details. Payment attempts retain the package, amount, M-PESA receipt, and status; phone numbers are masked after a terminal result and when beta/profile data is removed. Agree a finance-record retention schedule with the accountant and privacy lead before launch. The local development database and this repository's Render demo service are not live-payment environments.

### Data and file safeguards

- Staff pages require a Django staff account. Evidence files are stored outside the static website, are not exposed through a public media URL, and are served only to authenticated staff as downloads.
- Accepted evidence is PDF/JPG/PNG only, maximum 5 MB each and 20 documents (100 MB total) per registration/request. Images are re-encoded to remove embedded metadata. Production uploads require ClamAV scanning.
- Government ID images, group registration evidence, farm evidence, partner business evidence, and financial-analysis records can be uploaded only with a separate document-consent checkbox. Registration alone does not mark a person, group, farm, business, or financial statement as verified.
- Portal D assessment requests are manually scoped and quoted by staff. Any uploaded enterprise, market, production, or redacted financial summaries are private, require separate document consent, and follow the same size, file-validation, access, and retention controls as Portal C. Assessments are human-prepared and do not generate automated risk scores or make credit, investment, insurance, legal, or regulatory decisions.
- Research-invitation permission is a separate optional consent on farmer and partner registration. Existing records default to no permission. Staff must select an opted-in contact and manually deliver a study-specific invitation. Respondent participation requires study-specific consent.
- Research answers contain only fixed-choice values and an internal study identifier; they contain no profile, contact, IP address, or user-agent. Invitation/profile linkage is removed after submission. Researchers see no individual answers; results are withheld until at least five responses, with question distributions hidden when any non-zero answer category has fewer than five responses.
- Questionnaire response records are scheduled for deletion after one year; results are no longer available after that deletion because separate long-term result snapshots are not stored. Expired invitation records are deleted by the retention command. Researcher applications and their accounts/studies are scheduled for deletion after two years without recorded contact. Invitation links are single-use and expire after 14 days. No email or SMS delivery integration is configured; staff deliver approved invitations through their authorised contact workflow.
- The selected schedules are deletion of documents 365 days after upload and deletion of farmer, partner, financial-analysis, or risk-assessment requests after 730 days without recorded contact. Staff admin includes an action to update the last-contact date after an actual contact.
- Run `python manage.py purge_retained_data` to preview expired records. Run `python manage.py purge_retained_data --execute` to delete expired records and their private files. Schedule the execution command at least daily in production; protect backup copies with matching retention.
- The privacy notice, consent wording, lawful collection purpose, retention schedule, and identity-document handling must be reviewed and approved by MoFirms before real registrations open. Research ethics, researcher vetting and suspension, invitation delivery, response suppression, and participant-withdrawal procedures must also be approved before live research. Business-listing/referral consent is optional and does not create a public directory. Financial-analysis requests should collect approximate ranges only; do not collect personal ID numbers, tax PINs, bank credentials, passwords, or unrelated people's data through these forms.

### Production deployment checklist

Do not expose this service publicly until MoFirms has approved the data policy and configured a production environment:

1. Use PostgreSQL, HTTPS, a strong secret in `DJANGO_SECRET_KEY`, the exact production host in `DJANGO_ALLOWED_HOSTS`, and the matching origin in `DJANGO_CSRF_TRUSTED_ORIGINS`. If TLS terminates at a reverse proxy, set `DJANGO_TRUST_PROXY_SSL_HEADER=True` only when that trusted proxy strips and resets the forwarded-protocol header.
2. Set `DJANGO_DEBUG=False`, a shared Redis `REDIS_URL` for rate limits, and an encrypted private `PRIVATE_UPLOAD_ROOT` outside the code/repository directory. Keep database and file backups access-controlled and subject to the same retention schedule.
3. Run `python manage.py collectstatic` and configure the web server to publish only collected static files plus the site's public `/css/` and `/js/` assets. Never map `/private_uploads/` or `/private-media/` to a public URL.
4. Install ClamAV, keep its signatures current, set `ANTIVIRUS_ENABLED=True`, and configure `CLAMSCAN_COMMAND`. Configure a dedicated staff account for each reviewer; do not share administrator credentials.
5. Configure logging, monitoring, restore-tested backups, and a daily retention purge. Review access controls and consent/retention wording before inviting farmers.

The public website remains available as static files, but Portals A, B, C, D, and E submissions, research questionnaires, and staff review require the Django application. See `.env.example` for environment variable names.

### Free public demo on Render

The included `render.yaml` deploys a read-only Django demo. Set `DEMO_MODE=True` and `DJANGO_DEBUG=False`; all state-changing requests are rejected, including form submissions, logins, and uploads. The demo uses ephemeral SQLite and local cache only. Do not enter real personal information or upload real documents. Free Render services can sleep when idle, and their local files are not durable. This demo is for exploration with synthetic information only; it is not a production service.

Connect the GitHub repository to Render and deploy the Blueprint from `render.yaml`. Render will generate the secret key and provide the service hostname. The settings automatically allow that Render hostname and add its HTTPS origin for CSRF checks. For local read-only testing, set `DEMO_MODE=True` while leaving `DJANGO_DEBUG=True`.

## Website notes

- Edit service statuses and website copy in `js/app.js` and `index.html`.
- The existing general enquiry form opens the visitor's email app; it does not persist enquiries.
- Confirm contact details, logo, domain, privacy wording, and company sign-off before launch.
