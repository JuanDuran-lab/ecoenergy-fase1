import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.db import models
from django.utils import timezone


class UserProfile(models.Model):
    """
    Datos adicionales del usuario de Django.

    organization define el ámbito (scoping) de datos del usuario. Un
    superusuario puede no tener organización porque ve todo.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        verbose_name="usuario",
        on_delete=models.CASCADE,
        related_name="profile",
    )
    organization = models.ForeignKey(
        "monitoring.Organization",
        verbose_name="organización",
        on_delete=models.PROTECT,
        related_name="user_profiles",
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "user_profile"
        verbose_name = "perfil de usuario"
        verbose_name_plural = "perfiles de usuario"

    def __str__(self):
        organization = self.organization or "Todas las organizaciones"
        return f"{self.user.username} - {organization}"


class PasswordResetCode(models.Model):
    """
    Código numérico de 6 dígitos para recuperar la contraseña.

    - El código nunca se guarda en texto plano: se almacena su hash con
      el mismo algoritmo que usa Django para las contraseñas.
    - Expira a los EXPIRATION_MINUTES minutos.
    - Se bloquea después de MAX_ATTEMPTS intentos fallidos.
    - Al usarse con éxito se marca used_at y no puede reutilizarse.
    """

    CODE_LENGTH = 6
    EXPIRATION_MINUTES = 10
    MAX_ATTEMPTS = 5

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="usuario",
        on_delete=models.CASCADE,
        related_name="password_reset_codes",
    )
    code_hash = models.CharField("hash del código", max_length=128)
    created_at = models.DateTimeField("creado el", auto_now_add=True)
    expires_at = models.DateTimeField("expira el")
    used_at = models.DateTimeField("usado el", null=True, blank=True)
    attempts = models.PositiveSmallIntegerField("intentos fallidos", default=0)

    class Meta:
        db_table = "password_reset_code"
        verbose_name = "código de recuperación"
        verbose_name_plural = "códigos de recuperación"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} - {self.created_at:%d-%m-%Y %H:%M}"

    @classmethod
    def issue_for(cls, user):
        """
        Invalida los códigos pendientes del usuario y genera uno nuevo.
        Retorna (instancia, código_en_texto_plano). El texto plano solo
        existe en memoria para enviarlo por correo.
        """
        now = timezone.now()
        cls.objects.filter(user=user, used_at__isnull=True, expires_at__gt=now).update(
            expires_at=now
        )
        raw_code = f"{secrets.randbelow(10 ** cls.CODE_LENGTH):0{cls.CODE_LENGTH}d}"
        instance = cls.objects.create(
            user=user,
            code_hash=make_password(raw_code),
            expires_at=now + timedelta(minutes=cls.EXPIRATION_MINUTES),
        )
        return instance, raw_code

    @classmethod
    def latest_usable_for(cls, user):
        return (
            cls.objects.filter(
                user=user,
                used_at__isnull=True,
                expires_at__gt=timezone.now(),
                attempts__lt=cls.MAX_ATTEMPTS,
            )
            .order_by("-created_at")
            .first()
        )

    @property
    def is_usable(self):
        return (
            self.used_at is None
            and self.expires_at > timezone.now()
            and self.attempts < self.MAX_ATTEMPTS
        )

    def verify(self, raw_code):
        """Compara el código ingresado con el hash. Cuenta los fallos."""
        if not self.is_usable:
            return False
        if check_password(raw_code, self.code_hash):
            return True
        self.attempts = models.F("attempts") + 1
        self.save(update_fields=["attempts"])
        self.refresh_from_db(fields=["attempts"])
        return False

    def mark_used(self):
        self.used_at = timezone.now()
        self.save(update_fields=["used_at"])
