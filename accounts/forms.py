from django import forms
from django.contrib.auth.forms import AuthenticationForm, SetPasswordForm
from django.core.validators import RegexValidator

from .models import PasswordResetCode


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Usuario",
        widget=forms.TextInput(attrs={"autofocus": True, "class": "form-control"}),
    )
    password = forms.CharField(
        label="Contraseña",
        strip=False,
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )


class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField(
        label="Correo electrónico",
        widget=forms.EmailInput(attrs={"class": "form-control", "autofocus": True}),
    )


class PasswordResetConfirmForm(SetPasswordForm):
    """
    Pide el código de 6 dígitos y la nueva contraseña dos veces.

    Hereda de SetPasswordForm de Django, que:
    - compara new_password1 con new_password2,
    - ejecuta todos los AUTH_PASSWORD_VALIDATORS (largo mínimo 10,
      complejidad, contraseñas comunes, etc.),
    - guarda la contraseña con set_password() (hash, nunca texto plano).
    """

    code = forms.CharField(
        label="Código de verificación",
        min_length=PasswordResetCode.CODE_LENGTH,
        max_length=PasswordResetCode.CODE_LENGTH,
        validators=[RegexValidator(r"^\d{6}$", "El código debe tener 6 dígitos.")],
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "inputmode": "numeric",
                "autocomplete": "one-time-code",
                "autofocus": True,
            }
        ),
    )

    field_order = ["code", "new_password1", "new_password2"]

    INVALID_CODE_MESSAGE = "El código es inválido, expiró o ya fue utilizado."

    def __init__(self, user, *args, **kwargs):
        super().__init__(user, *args, **kwargs)
        self.reset_code = None
        for name in ("new_password1", "new_password2"):
            self.fields[name].widget.attrs["class"] = "form-control"

    def clean_code(self):
        code = self.cleaned_data["code"]
        reset_code = (
            PasswordResetCode.latest_usable_for(self.user) if self.user else None
        )
        if reset_code is None or not reset_code.verify(code):
            raise forms.ValidationError(self.INVALID_CODE_MESSAGE, code="invalid_code")
        self.reset_code = reset_code
        return code

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            # El código queda marcado como usado: no puede reutilizarse.
            self.reset_code.mark_used()
        return user
