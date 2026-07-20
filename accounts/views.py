from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import (
    AccountSettingsForm,
    LoginForm,
    RegisterForm,
)


def register_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():
            user = form.save()

            login(
                request,
                user,
                backend="django.contrib.auth.backends.ModelBackend",
            )

            messages.success(
                request,
                "Your account was created successfully.",
            )

            return redirect("dashboard")
    else:
        form = RegisterForm()

    return render(
        request,
        "accounts/register.html",
        {
            "form": form,
        },
    )


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = LoginForm(
            request=request,
            data=request.POST,
        )

        if form.is_valid():
            user = form.get_user()
            login(request, user)

            messages.success(
                request,
                f"Welcome back, {user.username}.",
            )

            next_url = request.GET.get("next")

            if next_url:
                return redirect(next_url)

            return redirect("dashboard")

        messages.error(
            request,
            "Invalid username or password.",
        )
    else:
        form = LoginForm(request=request)

    return render(
        request,
        "accounts/login.html",
        {
            "form": form,
        },
    )


@login_required
def account_settings_view(request):
    if request.method == "POST":
        form = AccountSettingsForm(
            request.POST,
            request.FILES,
            instance=request.user,
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Your account settings were updated successfully.",
            )

            return redirect("account_settings")
    else:
        form = AccountSettingsForm(
            instance=request.user,
        )

    return render(
        request,
        "accounts/account_settings.html",
        {
            "form": form,
        },
    )


@login_required
def remove_company_logo(request):
    if request.method == "POST":
        user = request.user

        if user.company_logo:
            user.company_logo.delete(
                save=False
            )

            user.company_logo = None
            user.save(
                update_fields=[
                    "company_logo",
                ]
            )

            messages.success(
                request,
                "Company logo removed.",
            )

    return redirect(
        "account_settings"
    )


@login_required
def logout_view(request):
    if request.method == "POST":
        logout(request)

        messages.success(
            request,
            "You have been logged out.",
        )

        return redirect("login")

    return redirect("dashboard")
