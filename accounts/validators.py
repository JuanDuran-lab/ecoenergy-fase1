"""
Validador de complejidad de contraseñas.

Se registra en AUTH_PASSWORD_VALIDATORS (settings.py), por lo que Django
lo aplica automáticamente en SetPasswordForm, en el Admin y en
validate_password(). Complementa a MinimumLengthValidator (mínimo 10).
"""

import re

from django.core.exceptions import ValidationError

SPECIAL_CHARACTERS = r"""!"#$%&'()*+,-./:;<=>?@[\]^_`{|}~"""


class PasswordComplexityValidator:
    rules = (
        (r"[A-Z]", "password_no_upper", "al menos una letra mayúscula"),
        (r"[a-z]", "password_no_lower", "al menos una letra minúscula"),
        (r"\d", "password_no_digit", "al menos un número"),
        (
            "[" + re.escape(SPECIAL_CHARACTERS) + "]",
            "password_no_special",
            "al menos un carácter especial (por ejemplo ! # $ % & * ?)",
        ),
    )

    def validate(self, password, user=None):
        errors = [
            ValidationError(f"La contraseña debe contener {message}.", code=code)
            for pattern, code, message in self.rules
            if not re.search(pattern, password)
        ]
        if errors:
            raise ValidationError(errors)

    def get_help_text(self):
        return (
            "La contraseña debe contener mayúsculas, minúsculas, números "
            "y al menos un carácter especial."
        )
