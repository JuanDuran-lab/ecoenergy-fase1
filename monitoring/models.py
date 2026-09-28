import uuid
from decimal import Decimal
from pathlib import Path

from django.core.exceptions import ValidationError
from django.core.validators import (
    FileExtensionValidator,
    MaxValueValidator,
    MinValueValidator,
    RegexValidator,
)
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone

from core.models import SoftDeleteModel

from .validators import (
    ALLOWED_IMAGE_EXTENSIONS,
    validate_image_content,
    validate_image_size,
)

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


class Manufacturer(SoftDeleteModel):
    name = models.CharField("nombre", max_length=120)
    country = models.CharField("país", max_length=80, blank=True)
    website = models.URLField("sitio web", blank=True)
    is_active = models.BooleanField("activo", default=True)

    class Meta:
        db_table = "manufacturer"
        verbose_name = "fabricante"
        verbose_name_plural = "fabricantes"
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["name"], condition=ALIVE, name="uq_manufacturer_name_alive"
            )
        ]

    def __str__(self):
        return self.name


class AlertSeverity(SoftDeleteModel):
    name = models.CharField("nombre", max_length=50)
    level = models.PositiveSmallIntegerField(
        "nivel",
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="1 = más leve, 5 = más grave.",
    )
    color = models.CharField(
        "color",
        max_length=7,
        default="#6c757d",
        validators=[
            RegexValidator(r"^#[0-9a-fA-F]{6}$", "Use un color hexadecimal, ej: #dc3545.")
        ],
    )
    description = models.TextField("descripción", blank=True)

    class Meta:
        db_table = "alert_severity"
        verbose_name = "severidad de alerta"
        verbose_name_plural = "severidades de alerta"
        ordering = ["level"]
        constraints = [
            models.UniqueConstraint(
                fields=["name"], condition=ALIVE, name="uq_alert_severity_name_alive"
            ),
            models.UniqueConstraint(
                fields=["level"], condition=ALIVE, name="uq_alert_severity_level_alive"
            ),
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

    def get_absolute_url(self):
        return reverse("monitoring:zone_detail", args=[self.pk])

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
        """
        Borrado lógico en cascada: al eliminar una zona también se
        eliminan (lógicamente) sus dispositivos, lecturas y alertas.
        """
        ConsumptionReading.objects.filter(device__zone=self).soft_delete()
        Alert.objects.filter(zone=self).soft_delete()
        self.devices.all().soft_delete()
        super().soft_delete()


def device_image_path(instance, filename):
    """Nombre aleatorio para evitar colisiones y nombres maliciosos."""
    extension = Path(filename).suffix.lower()
    return f"devices/{uuid.uuid4().hex}{extension}"


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
    manufacturer = models.ForeignKey(
        Manufacturer,
        verbose_name="fabricante",
        on_delete=models.PROTECT,
        related_name="devices",
    )
    name = models.CharField("nombre", max_length=120)
    serial_number = models.CharField(
        "número de serie",
        max_length=40,
        validators=[
            RegexValidator(
                r"^[A-Z0-9-]{4,40}$",
                "Solo mayúsculas, números y guiones (4 a 40 caracteres).",
            )
        ],
    )
    nominal_consumption_kwh = models.DecimalField(
        "consumo nominal (kWh)",
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01")), MaxValueValidator(Decimal("5000"))],
        help_text="Consumo energético nominal del dispositivo en kWh (0,01 a 5.000).",
    )
    installed_on = models.DateField("fecha de instalación")
    is_active = models.BooleanField("activo", default=True)
    image = models.ImageField(
        "imagen",
        upload_to=device_image_path,
        blank=True,
        validators=[
            FileExtensionValidator(ALLOWED_IMAGE_EXTENSIONS),
            validate_image_size,
            validate_image_content,
        ],
        help_text="JPG, PNG o WEBP. Máximo 2 MB.",
    )

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
            ),
            models.UniqueConstraint(
                fields=["serial_number"],
                condition=ALIVE,
                name="uq_device_serial_number_alive",
            ),
        ]

    def __str__(self):
        return f"{self.name} - {self.zone.name}"

    def get_absolute_url(self):
        return reverse("monitoring:device_detail", args=[self.pk])

    def clean(self):
        super().clean()
        if self.installed_on and self.installed_on > timezone.localdate():
            raise ValidationError(
                {"installed_on": "La fecha de instalación no puede ser futura."}
            )

    def soft_delete(self):
        """Borrado lógico en cascada: lecturas y alertas del dispositivo."""
        self.readings.all().soft_delete()
        self.alerts.all().soft_delete()
        super().soft_delete()


class ConsumptionReading(SoftDeleteModel):
    organization_lookup = "device__zone__organization"

    MAX_CONSUMPTION_KWH = Decimal("10000")

    device = models.ForeignKey(
        Device,
        verbose_name="dispositivo",
        on_delete=models.PROTECT,
        related_name="readings",
    )
    reading_at = models.DateTimeField("fecha y hora de lectura")
    consumption_kwh = models.DecimalField(
        "consumo (kWh)",
        max_digits=10,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal("0")),
            MaxValueValidator(MAX_CONSUMPTION_KWH),
        ],
    )
    notes = models.CharField("observaciones", max_length=255, blank=True)

    class Meta:
        db_table = "consumption_reading"
        verbose_name = "lectura de consumo"
        verbose_name_plural = "lecturas de consumo"
        ordering = ["-reading_at"]
        permissions = [
            ("export_consumptionreading", "Puede exportar lecturas a Excel"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["device", "reading_at"],
                condition=ALIVE,
                name="uq_reading_device_datetime_alive",
            )
        ]
        indexes = [models.Index(fields=["device", "reading_at"])]

    def __str__(self):
        return f"{self.device.name} - {self.reading_at:%d-%m-%Y %H:%M}"

    def get_absolute_url(self):
        return reverse("monitoring:reading_detail", args=[self.pk])

    @property
    def is_over_nominal(self):
        return self.consumption_kwh > self.device.nominal_consumption_kwh

    def clean(self):
        super().clean()
        errors = {}

        if self.reading_at and self.reading_at > timezone.now():
            errors["reading_at"] = "La lectura no puede tener fecha futura."

        # Regla de negocio: no se registran lecturas nuevas en dispositivos
        # inactivos. Las lecturas históricas sí pueden editarse.
        if self._state.adding and self.device_id and not self.device.is_active:
            errors["device"] = "No se pueden registrar lecturas de un dispositivo inactivo."

        if errors:
            raise ValidationError(errors)


class Alert(SoftDeleteModel):
    organization_lookup = "zone__organization"

    class Status(models.TextChoices):
        OPEN = "open", "Abierta"
        IN_PROGRESS = "in_progress", "En revisión"
        RESOLVED = "resolved", "Resuelta"

    zone = models.ForeignKey(
        Zone,
        verbose_name="zona",
        on_delete=models.PROTECT,
        related_name="alerts",
    )
    device = models.ForeignKey(
        Device,
        verbose_name="dispositivo",
        on_delete=models.PROTECT,
        related_name="alerts",
        null=True,
        blank=True,
    )
    reading = models.ForeignKey(
        ConsumptionReading,
        verbose_name="lectura que la originó",
        on_delete=models.SET_NULL,
        related_name="alerts",
        null=True,
        blank=True,
    )
    severity = models.ForeignKey(
        AlertSeverity,
        verbose_name="severidad",
        on_delete=models.PROTECT,
        related_name="alerts",
    )
    title = models.CharField("título", max_length=150)
    description = models.TextField("descripción", blank=True)
    status = models.CharField(
        "estado", max_length=20, choices=Status.choices, default=Status.OPEN
    )
    detected_at = models.DateTimeField("detectada el")
    resolved_at = models.DateTimeField("resuelta el", null=True, blank=True)

    class Meta:
        db_table = "alert"
        verbose_name = "alerta"
        verbose_name_plural = "alertas"
        ordering = ["-detected_at"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("monitoring:alert_detail", args=[self.pk])

    def clean(self):
        super().clean()
        errors = {}

        if self.device_id and self.zone_id and self.device.zone_id != self.zone_id:
            errors["device"] = "El dispositivo no pertenece a la zona seleccionada."

        if (
            self.reading_id
            and self.device_id
            and "device" not in errors
            and self.reading.device_id != self.device_id
        ):
            errors["device"] = (
                "La lectura que originó la alerta pertenece a otro dispositivo."
            )

        if self.detected_at and self.detected_at > timezone.now():
            errors["detected_at"] = "La fecha de detección no puede ser futura."

        if self.status == self.Status.RESOLVED:
            if not self.resolved_at:
                errors["resolved_at"] = "Una alerta resuelta debe indicar la fecha de resolución."
            elif self.detected_at and self.resolved_at < self.detected_at:
                errors["resolved_at"] = "La resolución no puede ser anterior a la detección."
        elif self.resolved_at:
            errors["resolved_at"] = "Solo una alerta resuelta puede tener fecha de resolución."

        if errors:
            raise ValidationError(errors)
