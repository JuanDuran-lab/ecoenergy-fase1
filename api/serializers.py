"""
Serializers de la API REST, con campos explícitos.

Principales (CRUD): ZoneSerializer, DeviceSerializer, ManufacturerSerializer
y CategorySerializer. Operacionales (solo lectura): ConsumptionReadingSerializer
y AlertSerializer.

Validaciones (respuesta 400):
- De campo: formato del número de serie, rangos de kWh y fecha de instalación
  no futura (validadores y clean() del modelo, los mismos de la web).
- De relación: la zona de un dispositivo y la organización de una zona deben
  pertenecer a la organización del usuario (scoping); no se aceptan
  categorías ni fabricantes inactivos ni nombres duplicados.
"""

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from core.scoping import get_user_organization, scope_queryset
from monitoring.models import (
    Alert,
    Category,
    ConsumptionReading,
    Device,
    Manufacturer,
    Organization,
    Zone,
)

OUT_OF_SCOPE = "El registro {pk_value} no existe o no pertenece a tu organización."


def normalize_spaces(value):
    return " ".join(value.split())


class DomainModelSerializer(serializers.ModelSerializer):
    """Base de los serializers con escritura: usuario actual y reglas del modelo."""

    @property
    def user(self):
        request = self.context.get("request")
        return getattr(request, "user", None)

    def current_id(self, field_name):
        if self.instance is None:
            return None
        return getattr(self.instance, f"{field_name}_id", None)

    def check_active(self, attrs, field_name, message):
        value = attrs.get(field_name)
        if value is not None and not value.is_active and value.pk != self.current_id(field_name):
            raise serializers.ValidationError({field_name: message})

    def check_duplicate(self, queryset, message, field_name=None):
        # field_name solo se indica desde validate(); en validate_<campo>
        # DRF ya asocia el error al campo.
        if self.instance is not None:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError(
                {field_name: message} if field_name else message
            )

    def run_model_validation(self, attrs):
        # Aplica clean() y las restricciones del modelo, igual que el
        # formulario web, y entrega sus errores como 400 en JSON.
        instance = self.instance or self.Meta.model()
        for name, value in attrs.items():
            setattr(instance, name, value)
        try:
            instance.clean()
            instance.validate_constraints()
        except DjangoValidationError as error:
            raise serializers.ValidationError(serializers.as_serializer_error(error))


# ---------------------------------------------------------------------------
# Principales
# ---------------------------------------------------------------------------


class ZoneSerializer(DomainModelSerializer):
    organization = serializers.PrimaryKeyRelatedField(
        queryset=Organization.objects.none(),
        required=False,
        error_messages={"does_not_exist": OUT_OF_SCOPE},
    )
    organization_name = serializers.CharField(source="organization.name", read_only=True)
    zone_type_name = serializers.CharField(source="zone_type.name", read_only=True)
    status_name = serializers.CharField(source="status.name", read_only=True)

    class Meta:
        model = Zone
        fields = [
            "id",
            "organization",
            "organization_name",
            "name",
            "zone_type",
            "zone_type_name",
            "status",
            "status_name",
            "consumption_limit_kwh",
            "description",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        user = self.user
        if user is None:
            return
        if user.is_superuser:
            organizations = Organization.objects.filter(is_active=True)
        else:
            organization = get_user_organization(user)
            organizations = Organization.objects.filter(
                pk=getattr(organization, "pk", None)
            )
        self.fields["organization"].queryset = organizations

    def validate_name(self, value):
        return normalize_spaces(value)

    def validate(self, attrs):
        if self.instance is None and "organization" not in attrs:
            attrs["organization"] = get_user_organization(self.user)

        organization = attrs.get("organization") or getattr(self.instance, "organization", None)
        if organization is None:
            raise serializers.ValidationError(
                {"organization": "Tu usuario no tiene una organización asignada."}
            )

        self.check_active(attrs, "zone_type", "El tipo de zona está inactivo.")

        name = attrs.get("name", getattr(self.instance, "name", None))
        if name:
            self.check_duplicate(
                Zone.objects.filter(organization=organization, name__iexact=name),
                "Ya existe una zona con este nombre en la organización.",
                field_name="name",
            )

        self.run_model_validation(attrs)
        return attrs


class DeviceSerializer(DomainModelSerializer):
    zone = serializers.PrimaryKeyRelatedField(
        queryset=Zone.objects.none(),
        error_messages={"does_not_exist": OUT_OF_SCOPE},
    )
    zone_name = serializers.CharField(source="zone.name", read_only=True)
    organization = serializers.IntegerField(source="zone.organization_id", read_only=True)
    organization_name = serializers.CharField(
        source="zone.organization.name", read_only=True
    )
    category_name = serializers.CharField(source="category.name", read_only=True)
    manufacturer_name = serializers.CharField(source="manufacturer.name", read_only=True)

    class Meta:
        model = Device
        fields = [
            "id",
            "zone",
            "zone_name",
            "organization",
            "organization_name",
            "name",
            "serial_number",
            "category",
            "category_name",
            "manufacturer",
            "manufacturer_name",
            "nominal_consumption_kwh",
            "installed_on",
            "is_active",
            "image",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["image", "created_at", "updated_at"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.user is not None:
            self.fields["zone"].queryset = scope_queryset(
                Zone.objects.select_related("organization"), self.user
            )

    def validate_name(self, value):
        return normalize_spaces(value)

    def validate_serial_number(self, value):
        serial = value.strip().upper()
        self.check_duplicate(
            Device.objects.filter(serial_number=serial),
            "Ya existe un dispositivo con este número de serie.",
        )
        return serial

    def validate(self, attrs):
        self.check_active(attrs, "category", "La categoría está inactiva.")
        self.check_active(attrs, "manufacturer", "El fabricante está inactivo.")

        zone = attrs.get("zone", getattr(self.instance, "zone", None))
        name = attrs.get("name", getattr(self.instance, "name", None))
        if zone and name:
            self.check_duplicate(
                Device.objects.filter(zone=zone, name__iexact=name),
                "Ya existe un dispositivo con este nombre en la zona.",
                field_name="name",
            )

        self.run_model_validation(attrs)
        return attrs


class ManufacturerSerializer(DomainModelSerializer):
    class Meta:
        model = Manufacturer
        fields = [
            "id",
            "name",
            "country",
            "website",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def validate_name(self, value):
        name = normalize_spaces(value)
        self.check_duplicate(
            Manufacturer.objects.filter(name__iexact=name),
            "Ya existe un fabricante con este nombre.",
        )
        return name

    def validate(self, attrs):
        self.run_model_validation(attrs)
        return attrs


class CategorySerializer(DomainModelSerializer):
    class Meta:
        model = Category
        fields = [
            "id",
            "name",
            "description",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def validate_name(self, value):
        name = normalize_spaces(value)
        self.check_duplicate(
            Category.objects.filter(name__iexact=name),
            "Ya existe una categoría con este nombre.",
        )
        return name

    def validate(self, attrs):
        self.run_model_validation(attrs)
        return attrs


# ---------------------------------------------------------------------------
# Operacionales (solo lectura)
# ---------------------------------------------------------------------------


class ConsumptionReadingSerializer(serializers.ModelSerializer):
    device_name = serializers.CharField(source="device.name", read_only=True)
    zone = serializers.IntegerField(source="device.zone_id", read_only=True)
    zone_name = serializers.CharField(source="device.zone.name", read_only=True)
    organization_name = serializers.CharField(
        source="device.zone.organization.name", read_only=True
    )
    nominal_consumption_kwh = serializers.DecimalField(
        source="device.nominal_consumption_kwh",
        max_digits=10,
        decimal_places=2,
        read_only=True,
    )
    is_over_nominal = serializers.BooleanField(read_only=True)

    class Meta:
        model = ConsumptionReading
        fields = [
            "id",
            "device",
            "device_name",
            "zone",
            "zone_name",
            "organization_name",
            "reading_at",
            "consumption_kwh",
            "nominal_consumption_kwh",
            "is_over_nominal",
            "notes",
            "created_at",
        ]
        read_only_fields = fields


class AlertSerializer(serializers.ModelSerializer):
    zone_name = serializers.CharField(source="zone.name", read_only=True)
    organization_name = serializers.CharField(
        source="zone.organization.name", read_only=True
    )
    device_name = serializers.CharField(source="device.name", read_only=True, default=None)
    severity_name = serializers.CharField(source="severity.name", read_only=True)
    severity_level = serializers.IntegerField(source="severity.level", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Alert
        fields = [
            "id",
            "zone",
            "zone_name",
            "organization_name",
            "device",
            "device_name",
            "reading",
            "severity",
            "severity_name",
            "severity_level",
            "title",
            "description",
            "status",
            "status_display",
            "detected_at",
            "resolved_at",
        ]
        read_only_fields = fields
