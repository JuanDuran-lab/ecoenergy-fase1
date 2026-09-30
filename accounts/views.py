"""
Login, logout y recuperación de contraseña.

Recuperación en dos pasos:
1. El usuario ingresa su correo y recibe un código de 6 dígitos. La
   respuesta es la misma exista o no el correo (no revela usuarios).
2. Ingresa el código y la nueva contraseña, validada con las mismas
   reglas de settings.AUTH_PASSWORD_VALIDATORS.
"""

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.views import LoginView, LogoutView
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.views.decorators.http import require_http_methods

from .forms import LoginForm, PasswordResetConfirmForm, PasswordResetRequestForm
from .models import PasswordResetCode

SESSION_RESET_EMAIL = "password_reset_email"


class EcoLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True


class EcoLogoutView(LogoutView):
    next_page = reverse_lazy("accounts:login")


def send_reset_code_email(user, raw_code):
    context = {
        "user": user,
        "code": raw_code,
        "minutes": PasswordResetCode.EXPIRATION_MINUTES,
    }
    send_mail(
        subject="EcoEnergy - Código para recuperar tu contraseña",
        message=render_to_string("accounts/email/password_reset_code.txt", context),
        from_email=None,
        recipient_list=[user.email],
    )


@require_http_methods(["GET", "POST"])
def password_reset_request(request):
    form = PasswordResetRequestForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        email = form.cleaned_data["email"]
        user = (
            get_user_model()
            .objects.filter(email__iexact=email, is_active=True)
            .order_by("pk")
            .first()
        )
        if user is not None:
            _, raw_code = PasswordResetCode.issue_for(user)
            send_reset_code_email(user, raw_code)

        request.session[SESSION_RESET_EMAIL] = email
        messages.info(
            request,
            "Si el correo está registrado, te enviamos un código de 6 dígitos. "
            f"El código expira en {PasswordResetCode.EXPIRATION_MINUTES} minutos.",
        )
        return redirect("accounts:password_reset_confirm")

    return render(request, "accounts/password_reset_request.html", {"form": form})


@require_http_methods(["GET", "POST"])
def password_reset_confirm(request):
    email = request.session.get(SESSION_RESET_EMAIL)
    if not email:
        messages.warning(request, "Primero ingresa tu correo para recibir un código.")
        return redirect("accounts:password_reset_request")

    user = (
        get_user_model()
        .objects.filter(email__iexact=email, is_active=True)
        .order_by("pk")
        .first()
    )
    form = PasswordResetConfirmForm(user, request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        request.session.pop(SESSION_RESET_EMAIL, None)
        messages.success(
            request, "Tu contraseña fue actualizada. Ya puedes iniciar sesión."
        )
        return redirect("accounts:login")

    return render(
        request,
        "accounts/password_reset_confirm.html",
        {"form": form, "email": email},
    )
