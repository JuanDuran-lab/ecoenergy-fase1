from django.conf import settings
from django.db import models


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
