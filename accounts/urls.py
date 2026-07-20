from django.urls import path

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
