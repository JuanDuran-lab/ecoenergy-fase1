from decimal import Decimal

from django import forms

from core.scoping import get_user_organization, scope_queryset

from .models import (
    Alert,
    AlertSeverity,
    Category,
    ConsumptionReading,
    Device,
    Manufacturer,
    Organization,
    Zone,
    ZoneStatus,
    ZoneType,
)

DATETIME_FORMAT = "%Y-%m-%dT%H:%M"


class BootstrapFormMixin:
    def apply_bootstrap(self):
        for field in self.fields.values():
            if isinstance(field, forms.ModelChoiceField):
                field.empty_label = "Seleccione una opción"
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                css = "form-check-input"
            elif isinstance(widget, forms.Select):
                css = "form-select"
            else:
                css = "form-control"
            widget.attrs["class"] = f"{widget.attrs.get('class', '')} {css}".strip()


class ScopedModelForm(BootstrapFormMixin, forms.ModelForm):
    def __init__(self, *args, user, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        self.apply_bootstrap()

    def active_master(self, model, field_name):
        queryset = model.objects.filter(is_active=True)
        current = getattr(self.instance, f"{field_name}_id", None)
        if current:
            queryset = model.objects.filter(pk=current) | queryset
        return queryset.distinct()


class ZoneForm(ScopedModelForm):
    class Meta:
        model = Zone
        fields = [
            "organization",
            "name",
            "zone_type",
            "status",
            "consumption_limit_kwh",
            "description",
        ]
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["zone_type"].queryset = self.active_master(ZoneType, "zone_type")
        self.fields["status"].queryset = ZoneStatus.objects.all()

        if self.user.is_superuser:
            self.fields["organization"].queryset = Organization.objects.filter(is_active=True)
        else:
            del self.fields["organization"]
            if not self.instance.pk:
                self.instance.organization = get_user_organization(self.user)

    def clean_name(self):
        return " ".join(self.cleaned_data["name"].split())

    def clean(self):
        cleaned_data = super().clean()
        organization = cleaned_data.get("organization") or getattr(
            self.instance, "organization", None
        )
        if organization is None:
            raise forms.ValidationError("Tu usuario no tiene una organización asignada.")

        name = cleaned_data.get("name")
        if name:
            duplicates = Zone.objects.filter(organization=organization, name__iexact=name)
            if self.instance.pk:
                duplicates = duplicates.exclude(pk=self.instance.pk)
            if duplicates.exists():
                self.add_error("name", "Ya existe una zona con este nombre en la organización.")
        return cleaned_data


class DeviceForm(ScopedModelForm):
    class Meta:
        model = Device
        fields = [
            "zone",
            "name",
            "serial_number",
            "category",
            "manufacturer",
            "nominal_consumption_kwh",
            "installed_on",
            "is_active",
            "image",
        ]
        widgets = {
            "installed_on": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "image": forms.ClearableFileInput(attrs={"accept": "image/jpeg,image/png,image/webp"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["zone"].queryset = scope_queryset(
            Zone.objects.select_related("organization"), self.user
        )
        self.fields["category"].queryset = self.active_master(Category, "category")
        self.fields["manufacturer"].queryset = self.active_master(Manufacturer, "manufacturer")
        self.fields["serial_number"].help_text = "Ej: EE-76-00001"

    def clean_serial_number(self):
        serial = self.cleaned_data["serial_number"].strip().upper()
        duplicates = Device.objects.filter(serial_number=serial)
        if self.instance.pk:
            duplicates = duplicates.exclude(pk=self.instance.pk)
        if duplicates.exists():
            raise forms.ValidationError("Ya existe un dispositivo con este número de serie.")
        return serial

    def clean(self):
        cleaned_data = super().clean()
        zone = cleaned_data.get("zone")
        name = cleaned_data.get("name")
        if zone and name:
            duplicates = Device.objects.filter(zone=zone, name__iexact=name.strip())
            if self.instance.pk:
                duplicates = duplicates.exclude(pk=self.instance.pk)
            if duplicates.exists():
                self.add_error("name", "Ya existe un dispositivo con este nombre en la zona.")
        return cleaned_data


class ConsumptionReadingForm(ScopedModelForm):
    MAX_NOMINAL_FACTOR = Decimal("3")

    class Meta:
        model = ConsumptionReading
        fields = ["device", "reading_at", "consumption_kwh", "notes"]
        widgets = {
            "reading_at": forms.DateTimeInput(
                attrs={"type": "datetime-local"}, format=DATETIME_FORMAT
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        devices = scope_queryset(Device.objects.select_related("zone"), self.user)
        if not self.instance.pk:
            devices = devices.filter(is_active=True)
        self.fields["device"].queryset = devices.order_by("zone__name", "name")

    def clean(self):
        cleaned_data = super().clean()
        device = cleaned_data.get("device")
        reading_at = cleaned_data.get("reading_at")
        consumption = cleaned_data.get("consumption_kwh")

        if device and reading_at:
            duplicates = ConsumptionReading.objects.filter(device=device, reading_at=reading_at)
            if self.instance.pk:
                duplicates = duplicates.exclude(pk=self.instance.pk)
            if duplicates.exists():
                self.add_error(
                    "reading_at", "Ya existe una lectura de este dispositivo en esa fecha y hora."
                )

        if device and consumption is not None:
            limit = device.nominal_consumption_kwh * self.MAX_NOMINAL_FACTOR
            if consumption > limit:
                self.add_error(
                    "consumption_kwh",
                    f"Valor anómalo: supera 3 veces el consumo nominal del dispositivo "
                    f"({limit:.2f} kWh). Revise la lectura.",
                )
        return cleaned_data


class AlertForm(ScopedModelForm):
    class Meta:
        model = Alert
        fields = [
            "zone",
            "device",
            "severity",
            "title",
            "status",
            "detected_at",
            "resolved_at",
            "description",
        ]
        widgets = {
            "detected_at": forms.DateTimeInput(
                attrs={"type": "datetime-local"}, format=DATETIME_FORMAT
            ),
            "resolved_at": forms.DateTimeInput(
                attrs={"type": "datetime-local"}, format=DATETIME_FORMAT
            ),
            "description": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["zone"].queryset = scope_queryset(Zone.objects.all(), self.user)
        self.fields["device"].queryset = scope_queryset(
            Device.objects.select_related("zone"), self.user
        ).order_by("zone__name", "name")
        self.fields["device"].label_from_instance = lambda d: f"{d.zone.name} · {d.name}"
        self.fields["severity"].queryset = AlertSeverity.objects.all()
        self.fields["device"].help_text = "Opcional. Debe pertenecer a la zona seleccionada."
        self.fields["resolved_at"].help_text = "Obligatoria solo si el estado es Resuelta."
