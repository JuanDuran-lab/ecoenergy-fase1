"""
Django Admin de EcoEnergy.

- Tablas maestras y operacionales registradas con list_display,
  search_fields, list_filter, ordering y list_select_related.
- Inline: dispositivos (DeviceInline) dentro de la zona.
- Acciones personalizadas: activar / desactivar dispositivos.
- Validación: clean() de los modelos, que el Admin ejecuta al guardar.
- Seguridad: las tablas operacionales aplican scoping por organización.
"""

from django.contrib import admin
from django.utils.html import format_html

from core.admin import OrganizationScopedAdminMixin, SoftDeleteAdmin

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

admin.site.site_header = "EcoEnergy - Administración"
admin.site.site_title = "EcoEnergy Admin"
admin.site.index_title = "Panel de administración EcoEnergy"


# ---------------------------------------------------------------------------
# Tablas maestras
# ---------------------------------------------------------------------------


@admin.register(Organization)
class OrganizationAdmin(SoftDeleteAdmin):
    list_display = ("name", "tax_id", "is_active")
    search_fields = ("name", "tax_id")
    list_filter = ("is_active",)
    ordering = ("name",)


@admin.register(Category)
class CategoryAdmin(SoftDeleteAdmin):
    list_display = ("name", "is_active")
    search_fields = ("name", "description")
    list_filter = ("is_active",)
    ordering = ("name",)


@admin.register(ZoneType)
class ZoneTypeAdmin(SoftDeleteAdmin):
    list_display = ("name", "is_active")
    search_fields = ("name", "description")
    list_filter = ("is_active",)
    ordering = ("name",)


@admin.register(ZoneStatus)
class ZoneStatusAdmin(SoftDeleteAdmin):
    list_display = ("name",)
    search_fields = ("name", "description")
    ordering = ("name",)


@admin.register(Manufacturer)
class ManufacturerAdmin(SoftDeleteAdmin):
    list_display = ("name", "country", "website", "is_active")
    search_fields = ("name", "country")
    list_filter = ("is_active", "country")
    ordering = ("name",)


@admin.register(AlertSeverity)
class AlertSeverityAdmin(SoftDeleteAdmin):
    list_display = ("name", "level", "color_badge")
    search_fields = ("name",)
    ordering = ("level",)

    @admin.display(description="color")
    def color_badge(self, obj):
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;border-radius:4px">{}</span>',
            obj.color,
            obj.color,
        )


# ---------------------------------------------------------------------------
# Tablas operacionales (con scoping por organización)
# ---------------------------------------------------------------------------


class DeviceInline(admin.TabularInline):
    model = Device
    extra = 0
    fields = (
        "name",
        "serial_number",
        "category",
        "manufacturer",
        "nominal_consumption_kwh",
        "installed_on",
        "is_active",
    )
    show_change_link = True


@admin.register(Zone)
class ZoneAdmin(OrganizationScopedAdminMixin, SoftDeleteAdmin):
    list_display = (
        "name",
        "organization",
        "zone_type",
        "status",
        "consumption_limit_kwh",
    )
    search_fields = ("name", "description", "organization__name")
    list_filter = ("organization", "zone_type", "status")
    ordering = ("organization__name", "name")
    list_select_related = ("organization", "zone_type", "status")
    inlines = (DeviceInline,)


@admin.action(description="Activar dispositivos seleccionados")
def activate_devices(modeladmin, request, queryset):
    updated = queryset.update(is_active=True)
    modeladmin.message_user(request, f"{updated} dispositivo(s) activado(s).")


@admin.action(description="Desactivar dispositivos seleccionados")
def deactivate_devices(modeladmin, request, queryset):
    updated = queryset.update(is_active=False)
    modeladmin.message_user(request, f"{updated} dispositivo(s) desactivado(s).")


@admin.register(Device)
class DeviceAdmin(OrganizationScopedAdminMixin, SoftDeleteAdmin):
    list_display = (
        "name",
        "serial_number",
        "zone",
        "category",
        "manufacturer",
        "nominal_consumption_kwh",
        "is_active",
    )
    search_fields = ("name", "serial_number", "zone__name", "category__name")
    list_filter = ("is_active", "category", "manufacturer", "zone__organization")
    ordering = ("zone__name", "name")
    list_select_related = ("zone", "zone__organization", "category", "manufacturer")
    actions = SoftDeleteAdmin.actions + (activate_devices, deactivate_devices)
    scoped_fk_fields = {"zone": Zone}


@admin.register(ConsumptionReading)
class ConsumptionReadingAdmin(OrganizationScopedAdminMixin, SoftDeleteAdmin):
    list_display = ("device", "zone_name", "reading_at", "consumption_kwh")
    search_fields = ("device__name", "device__serial_number", "device__zone__name")
    list_filter = ("device__zone__organization", "device__category")
    date_hierarchy = "reading_at"
    ordering = ("-reading_at",)
    list_select_related = ("device", "device__zone")
    autocomplete_fields = ("device",)
    list_per_page = 30

    @admin.display(description="zona", ordering="device__zone__name")
    def zone_name(self, obj):
        return obj.device.zone.name


@admin.register(Alert)
class AlertAdmin(OrganizationScopedAdminMixin, SoftDeleteAdmin):
    list_display = ("title", "zone", "device", "severity", "status", "detected_at")
    search_fields = ("title", "description", "zone__name", "device__name")
    list_filter = ("status", "severity", "zone__organization")
    date_hierarchy = "detected_at"
    ordering = ("-detected_at",)
    list_select_related = ("zone", "device", "severity")
    autocomplete_fields = ("device", "reading")
    scoped_fk_fields = {"zone": Zone}
