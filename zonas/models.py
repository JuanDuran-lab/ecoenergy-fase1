from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models


class Organizacion(models.Model):
    nombre = models.CharField(max_length=150)
    rut = models.CharField(max_length=12, unique=True)
    activa = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Organización"
        verbose_name_plural = "Organizaciones"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    activa = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class TipoZona(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Tipo de zona"
        verbose_name_plural = "Tipos de zona"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class EstadoZona(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField(blank=True)

    class Meta:
        verbose_name = "Estado de zona"
        verbose_name_plural = "Estados de zona"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Zona(models.Model):
    organizacion = models.ForeignKey(
        Organizacion,
        on_delete=models.PROTECT,
        related_name="zonas",
    )

    tipo = models.ForeignKey(
        TipoZona,
        on_delete=models.PROTECT,
        related_name="zonas",
    )

    estado = models.ForeignKey(
        EstadoZona,
        on_delete=models.PROTECT,
        related_name="zonas",
    )

    nombre = models.CharField(max_length=120)

    descripcion = models.TextField(blank=True)

    limite_kwh = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Límite de consumo energético permitido para la zona.",
    )

    class Meta:
        verbose_name = "Zona"
        verbose_name_plural = "Zonas"
        ordering = ["organizacion__nombre", "nombre"]
        constraints = [
            models.UniqueConstraint(
                fields=["organizacion", "nombre"],
                name="uq_zona_organizacion_nombre",
            )
        ]

    def clean(self):
        super().clean()

        if self.limite_kwh is not None and self.limite_kwh <= 0:
            raise ValidationError(
                {
                    "limite_kwh": (
                        "El límite de consumo de una zona debe ser mayor que 0 kWh."
                    )
                }
            )

    def __str__(self):
        return f"{self.nombre} - {self.organizacion.nombre}"


class Dispositivo(models.Model):
    zona = models.ForeignKey(
        Zona,
        on_delete=models.PROTECT,
        related_name="dispositivos",
    )

    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name="dispositivos",
    )

    nombre = models.CharField(max_length=120)

    consumo_kwh = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Consumo energético del dispositivo en kWh.",
    )

    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Dispositivo"
        verbose_name_plural = "Dispositivos"
        ordering = ["zona__nombre", "nombre"]
        constraints = [
            models.UniqueConstraint(
                fields=["zona", "nombre"],
                name="uq_dispositivo_zona_nombre",
            )
        ]

    def __str__(self):
        return f"{self.nombre} - {self.zona.nombre}"


class PerfilUsuario(models.Model):
    usuario = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="perfil_ecoenergy",
    )

    organizacion = models.ForeignKey(
        Organizacion,
        on_delete=models.PROTECT,
        related_name="usuarios",
    )

    class Meta:
        verbose_name = "Perfil de usuario"
        verbose_name_plural = "Perfiles de usuario"

    def __str__(self):
        return f"{self.usuario.username} - {self.organizacion.nombre}"