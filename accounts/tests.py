"""
Pruebas de cuentas: política de contraseñas, login/logout y flujo completo
de recuperación de contraseña.
"""

import re
from datetime import timedelta

from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core import mail
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import PasswordResetCode

OLD_PASSWORD = "Antigua#Clave2026"
NEW_PASSWORD = "Nueva#Segura2026"


class PasswordPolicyTests(TestCase):
    def assert_rejected(self, password):
        with self.assertRaises(ValidationError):
            validate_password(password)

    def test_rejects_short_password(self):
        self.assert_rejected("Ab1#xyz")

    def test_rejects_without_uppercase(self):
        self.assert_rejected("sinmayuscula#2026")

    def test_rejects_without_lowercase(self):
        self.assert_rejected("SINMINUSCULA#2026")

    def test_rejects_without_digit(self):
        self.assert_rejected("SinNumeros#Clave")

    def test_rejects_without_special_character(self):
        self.assert_rejected("SinEspecial2026x")

    def test_accepts_strong_password(self):
        validate_password(NEW_PASSWORD)


class LoginLogoutTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("usuario", "usuario@test.cl", OLD_PASSWORD)

    def test_login_and_logout(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "usuario", "password": OLD_PASSWORD},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("_auth_user_id", self.client.session)

        response = self.client.post(reverse("accounts:logout"))
        self.assertRedirects(response, reverse("accounts:login"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_protected_view_redirects_to_login(self):
        response = self.client.get(reverse("monitoring:zone_list"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response["Location"])


class PasswordResetFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("usuario", "usuario@test.cl", OLD_PASSWORD)

    def request_code(self, email="usuario@test.cl"):
        mail.outbox.clear()
        self.client.post(reverse("accounts:password_reset_request"), {"email": email})
        if not mail.outbox:
            return None
        return re.search(r"\b(\d{6})\b", mail.outbox[0].body).group(1)

    def confirm(self, code, password1=NEW_PASSWORD, password2=NEW_PASSWORD):
        return self.client.post(
            reverse("accounts:password_reset_confirm"),
            {"code": code, "new_password1": password1, "new_password2": password2},
        )

    def test_full_flow_changes_password(self):
        code = self.request_code()
        self.assertIsNotNone(code)

        response = self.confirm(code)
        self.assertRedirects(response, reverse("accounts:login"))

        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(NEW_PASSWORD))

    def test_code_is_stored_hashed(self):
        code = self.request_code()
        stored = PasswordResetCode.objects.get(user=self.user)
        self.assertNotEqual(stored.code_hash, code)
        self.assertNotIn(code, stored.code_hash)

    def test_code_cannot_be_reused(self):
        code = self.request_code()
        self.confirm(code)

        session = self.client.session
        session["password_reset_email"] = "usuario@test.cl"
        session.save()
        response = self.confirm(code, "Otra#Clave20266", "Otra#Clave20266")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ya fue utilizado")
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(NEW_PASSWORD))

    def test_passwords_must_match(self):
        code = self.request_code()
        response = self.confirm(code, NEW_PASSWORD, "Distinta#Clave2026")
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(OLD_PASSWORD))

    def test_weak_password_is_rejected(self):
        code = self.request_code()
        response = self.confirm(code, "debil12345", "debil12345")
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(OLD_PASSWORD))

    def test_expired_code_is_rejected(self):
        code = self.request_code()
        PasswordResetCode.objects.update(expires_at=timezone.now() - timedelta(seconds=1))
        response = self.confirm(code)
        self.assertContains(response, "expiró")

    def test_new_request_invalidates_previous_code(self):
        first_code = self.request_code()
        second_code = self.request_code()
        if first_code != second_code:
            response = self.confirm(first_code)
            self.assertEqual(response.status_code, 200)
        response = self.confirm(second_code)
        self.assertRedirects(response, reverse("accounts:login"))

    def test_code_blocked_after_max_attempts(self):
        code = self.request_code()
        wrong = "000000" if code != "000000" else "111111"
        for _ in range(PasswordResetCode.MAX_ATTEMPTS):
            self.confirm(wrong)
        response = self.confirm(code)
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(OLD_PASSWORD))

    def test_unknown_email_gets_same_response(self):
        response = self.client.post(
            reverse("accounts:password_reset_request"), {"email": "nadie@test.cl"}
        )
        self.assertRedirects(response, reverse("accounts:password_reset_confirm"))
        self.assertEqual(len(mail.outbox), 0)
