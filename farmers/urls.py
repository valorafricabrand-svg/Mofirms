from django.urls import path

from . import views


urlpatterns = [
    path("register/", views.register_farmer, name="register_farmer"),
    path("registered/<str:reference>/", views.registration_success, name="registration_success"),
]
