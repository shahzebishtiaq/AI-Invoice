from django.contrib.auth import views as auth_views
from django.urls import path
from django.urls import reverse_lazy

from .forms import (
    CustomPasswordResetForm,
    CustomSetPasswordForm,
)
from .views import (
    account_settings_view,
    login_view,
    logout_view,
    register_view,
    remove_company_logo,
)


urlpatterns = [
    path(
        "register/",
        register_view,
        name="register",
    ),
    path(
        "login/",
        login_view,
        name="login",
    ),
    path(
        "logout/",
        logout_view,
        name="logout",
    ),

    # ---------------------------------------------------------
    # Forgot-password pages
    # ---------------------------------------------------------
    path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(
            template_name="accounts/password_reset_form.html",
            email_template_name="accounts/password_reset_email.html",
            subject_template_name=(
                "accounts/password_reset_subject.txt"
            ),
            form_class=CustomPasswordResetForm,
            success_url=reverse_lazy(
                "password_reset_done"
            ),
        ),
        name="password_reset",
    ),
    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name=(
                "accounts/password_reset_done.html"
            ),
        ),
        name="password_reset_done",
    ),
    path(
        "password-reset-confirm/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name=(
                "accounts/password_reset_confirm.html"
            ),
            form_class=CustomSetPasswordForm,
            success_url=reverse_lazy(
                "password_reset_complete"
            ),
        ),
        name="password_reset_confirm",
    ),
    path(
        "password-reset-complete/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name=(
                "accounts/password_reset_complete.html"
            ),
        ),
        name="password_reset_complete",
    ),

    path(
        "settings/",
        account_settings_view,
        name="account_settings",
    ),
    path(
        "settings/remove-logo/",
        remove_company_logo,
        name="remove_company_logo",
    ),
]