from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q

from core.models import SoftDeleteModel

ALIVE = Q(deleted_at__isnull=True)


# ---------------------------------------------------------------------------
# Tablas maestras
# ---------------------------------------------------------------------------


class Organization(SoftDeleteModel):
    name = models.CharField("nombre", max_length=150)
    tax_id = models.CharField("RUT", max_length=12)
    is_active = models.BooleanField("activa", default=True)

    class Meta:
        db_table = "organization"
        verbose_name = "organización"
        verbose_name_plural = "organizaciones"
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["tax_id"],
                condition=ALIVE,
                name="uq_organization_tax_id_alive",
            )
        ]

    def __str__(self):
        return self.name


class Category(SoftDeleteModel):
    name = models.CharField("nombre", max_length=100)
    description = models.TextField("descripción", blank=True)
    is_active = models.BooleanField("activa", default=True)

    class Meta:
        db_table = "category"
        verbose_name = "categoría"
        verbose_name_plural = "categorías"
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["name"], condition=ALIVE, name="uq_category_name_alive"
            )
        ]

    def __str__(self):
        return self.name


class ZoneType(SoftDeleteModel):
    name = models.CharField("nombre", max_length=100)
    description = models.TextField("descripción", blank=True)
    is_active = models.BooleanField("activo", default=True)

    class Meta:
        db_table = "zone_type"
        verbose_name = "tipo de zona"
        verbose_name_plural = "tipos de zona"
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["name"], condition=ALIVE, name="uq_zone_type_name_alive"
            )
        ]

    def __str__(self):
        return self.name


class ZoneStatus(SoftDeleteModel):
    name = models.CharField("nombre", max_length=50)
    description = models.TextField("descripción", blank=True)

    class Meta:
        db_table = "zone_status"
        verbose_name = "estado de zona"
        verbose_name_plural = "estados de zona"
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["name"], condition=ALIVE, name="uq_zone_status_name_alive"
            )
        ]

    def __str__(self):
        return self.name


# ---------------------------------------------------------------------------
# Tablas operacionales
# ---------------------------------------------------------------------------


class Zone(SoftDeleteModel):
    organization_lookup = "organization"

    organization = models.ForeignKey(
        Organization,
        verbose_name="organización",
        on_delete=models.PROTECT,
        related_name="zones",
    )
    zone_type = models.ForeignKey(
        ZoneType,
        verbose_name="tipo",
        on_delete=models.PROTECT,
        related_name="zones",
    )
    status = models.ForeignKey(
        ZoneStatus,
        verbose_name="estado",
        on_delete=models.PROTECT,
        related_name="zones",
    )
    name = models.CharField("nombre", max_length=120)
    description = models.TextField("descripción", blank=True)
    consumption_limit_kwh = models.DecimalField(
        "límite de consumo (kWh)",
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text="Límite de consumo energético permitido para la zona.",
    )

    class Meta:
        db_table = "zone"
        verbose_name = "zona"
        verbose_name_plural = "zonas"
        ordering = ["organization__name", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "name"],
                condition=ALIVE,
                name="uq_zone_organization_name_alive",
            )
        ]

    def __str__(self):
        return f"{self.name} - {self.organization.name}"

    def clean(self):
        super().clean()
        if (
            self.consumption_limit_kwh is not None
            and self.consumption_limit_kwh <= 0
        ):
            raise ValidationError(
                {
                    "consumption_limit_kwh": (
                        "El límite de consumo de una zona debe ser mayor que 0 kWh."
                    )
                }
            )

    def soft_delete(self):
        """Borrado lógico en cascada: la zona y sus dispositivos."""
        self.devices.all().soft_delete()
        super().soft_delete()


class Device(SoftDeleteModel):
    organization_lookup = "zone__organization"

    zone = models.ForeignKey(
        Zone,
        verbose_name="zona",
        on_delete=models.PROTECT,
        related_name="devices",
    )
    category = models.ForeignKey(
        Category,
        verbose_name="categoría",
        on_delete=models.PROTECT,
        related_name="devices",
    )
    name = models.CharField("nombre", max_length=120)
    nominal_consumption_kwh = models.DecimalField(
        "consumo nominal (kWh)",
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
        help_text="Consumo energético nominal del dispositivo en kWh.",
    )
    is_active = models.BooleanField("activo", default=True)

    class Meta:
        db_table = "device"
        verbose_name = "dispositivo"
        verbose_name_plural = "dispositivos"
        ordering = ["zone__name", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["zone", "name"],
                condition=ALIVE,
                name="uq_device_zone_name_alive",
            )
        ]

    def __str__(self):
        return f"{self.name} - {self.zone.name}"
