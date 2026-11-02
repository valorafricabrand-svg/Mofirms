from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve
from django.views.generic import TemplateView

from farmers.views import (
    download_document,
    download_financial_analysis_document,
    download_partner_document,
    download_risk_assessment_document,
)


urlpatterns = [
    path("", TemplateView.as_view(template_name="index.html"), name="home"),
    path("portal/", include("farmers.urls")),
    path(
        "staff/documents/<int:document_id>/download/",
        download_document,
        name="download_document",
    ),
    path(
        "staff/partner-documents/<int:document_id>/download/",
        download_partner_document,
        name="download_partner_document",
    ),
    path(
        "staff/financial-analysis-documents/<int:document_id>/download/",
        download_financial_analysis_document,
        name="download_financial_analysis_document",
    ),
    path(
        "staff/risk-assessment-documents/<int:document_id>/download/",
        download_risk_assessment_document,
        name="download_risk_assessment_document",
    ),
    path("staff/", admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += [
        re_path(
            r"^css/(?P<path>.*)$",
            serve,
            {"document_root": settings.BASE_DIR / "css"},
        ),
        re_path(
            r"^js/(?P<path>.*)$",
            serve,
            {"document_root": settings.BASE_DIR / "js"},
        ),
    ]
