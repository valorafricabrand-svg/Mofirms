from django.urls import path

from . import views


urlpatterns = [
    path("register/", views.register_farmer, name="register_farmer"),
    path("registered/<str:reference>/", views.registration_success, name="registration_success"),
    path("partners/register/", views.register_partner, name="register_partner"),
    path(
        "partners/registered/<str:reference>/",
        views.partner_registration_success,
        name="partner_registration_success",
    ),
]
