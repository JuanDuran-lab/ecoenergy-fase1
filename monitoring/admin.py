from django.contrib import admin

from core.admin import OrganizationScopedAdminMixin, SoftDeleteAdmin

from .models import (
    Category,
    Device,
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


# ---------------------------------------------------------------------------
# Tablas operacionales (con scoping por organización)
# ---------------------------------------------------------------------------


class DeviceInline(admin.TabularInline):
    model = Device
    extra = 0
    fields = ("name", "category", "nominal_consumption_kwh", "is_active")
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
        "zone",
        "category",
        "nominal_consumption_kwh",
        "is_active",
    )
    search_fields = ("name", "zone__name", "category__name")
    list_filter = ("is_active", "category", "zone__organization")
    ordering = ("zone__name", "name")
    list_select_related = ("zone", "zone__organization", "category")
    actions = SoftDeleteAdmin.actions + (activate_devices, deactivate_devices)
    scoped_fk_fields = {"zone": Zone}
