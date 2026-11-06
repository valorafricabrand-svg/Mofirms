from django.urls import path

from . import billing
from . import views


urlpatterns = [
    path("beta/<uuid:token>/", billing.redeem_beta_invite, name="redeem_beta_invite"),
    path("beta/access/<uuid:token>/", billing.beta_enrollment, name="beta_enrollment"),
    path("beta/checkout/<uuid:token>/", billing.beta_checkout, name="beta_checkout"),
    path("beta/payment-status/<uuid:token>/", billing.payment_status, name="payment_status"),
    path("payments/mpesa/callback/", billing.mpesa_callback, name="mpesa_callback"),
    path("register/", views.register_farmer, name="register_farmer"),
    path("registered/<str:reference>/", views.registration_success, name="registration_success"),
    path("partners/register/", views.register_partner, name="register_partner"),
    path(
        "partners/registered/<str:reference>/",
        views.partner_registration_success,
        name="partner_registration_success",
    ),
    path("financial-analysis/", views.request_financial_analysis, name="request_financial_analysis"),
    path(
        "financial-analysis/received/<str:reference>/",
        views.financial_analysis_success,
        name="financial_analysis_success",
    ),
    path("risk-assessment/", views.request_risk_assessment, name="request_risk_assessment"),
    path(
        "risk-assessment/received/<str:reference>/",
        views.risk_assessment_success,
        name="risk_assessment_success",
    ),
    path("research/register/", views.register_researcher, name="register_researcher"),
    path(
        "research/application-received/",
        views.researcher_application_received,
        name="researcher_application_received",
    ),
    path("research/login/", views.researcher_login, name="researcher_login"),
    path("research/dashboard/", views.researcher_dashboard, name="researcher_dashboard"),
    path(
        "research/respond/<uuid:token>/",
        views.respond_to_research_invitation,
        name="respond_to_research_invitation",
    ),
]
