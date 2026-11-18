from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

from . import views


app_name = "smart_hasibu"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("signup/", views.signup, name="signup"),
    path("login/", views.signin, name="login"),
    path("logout/", views.signout, name="logout"),
    path("export/", views.export_entries, name="export_entries"),
    path("entries/<int:pk>/edit/", views.entry_edit, name="entry_edit"),
    path("entries/<int:pk>/delete/", views.entry_delete, name="entry_delete"),
    path(
        "enterprises/<int:pk>/edit/",
        views.enterprise_edit,
        name="enterprise_edit",
    ),
    path(
        "enterprises/<int:pk>/delete/",
        views.enterprise_delete,
        name="enterprise_delete",
    ),
    path(
        "password/change/",
        auth_views.PasswordChangeView.as_view(
            template_name="smart_hasibu/password_change.html",
            success_url=reverse_lazy("smart_hasibu:password_change_done"),
        ),
        name="password_change",
    ),
    path(
        "password/change/done/",
        auth_views.PasswordChangeDoneView.as_view(
            template_name="smart_hasibu/password_change_done.html",
        ),
        name="password_change_done",
    ),
    path(
        "password/reset/",
        views.RateLimitedPasswordResetView.as_view(
            template_name="smart_hasibu/password_reset.html",
            email_template_name="smart_hasibu/password_reset_email.txt",
            subject_template_name="smart_hasibu/password_reset_subject.txt",
            success_url=reverse_lazy("smart_hasibu:password_reset_done"),
        ),
        name="password_reset",
    ),
    path(
        "password/reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="smart_hasibu/password_reset_done.html",
        ),
        name="password_reset_done",
    ),
    path(
        "password/reset/confirm/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="smart_hasibu/password_reset_confirm.html",
            success_url=reverse_lazy("smart_hasibu:password_reset_complete"),
        ),
        name="password_reset_confirm",
    ),
    path(
        "password/reset/complete/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="smart_hasibu/password_reset_complete.html",
        ),
        name="password_reset_complete",
    ),
]
