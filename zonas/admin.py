from django.contrib import admin

from .models import (
    Categoria,
    Dispositivo,
    EstadoZona,
    Organizacion,
    PerfilUsuario,
    TipoZona,
    Zona,
)


@admin.register(Organizacion)
class OrganizacionAdmin(admin.ModelAdmin):
    list_display = ("nombre", "rut", "activa")
    search_fields = ("nombre", "rut")
    list_filter = ("activa",)
    ordering = ("nombre",)


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "activa")
    search_fields = ("nombre", "descripcion")
    list_filter = ("activa",)
    ordering = ("nombre",)


@admin.register(TipoZona)
class TipoZonaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "activo")
    search_fields = ("nombre", "descripcion")
    list_filter = ("activo",)
    ordering = ("nombre",)


@admin.register(EstadoZona)
class EstadoZonaAdmin(admin.ModelAdmin):
    list_display = ("nombre",)
    search_fields = ("nombre", "descripcion")
    ordering = ("nombre",)


@admin.register(Zona)
class ZonaAdmin(admin.ModelAdmin):
    list_display = (
        "nombre",
        "organizacion",
        "tipo",
        "estado",
        "limite_kwh",
    )
    search_fields = (
        "nombre",
        "descripcion",
        "organizacion__nombre",
    )
    list_filter = (
        "organizacion",
        "tipo",
        "estado",
    )
    ordering = (
        "organizacion__nombre",
        "nombre",
    )
    list_select_related = (
        "organizacion",
        "tipo",
        "estado",
    )


@admin.register(Dispositivo)
class DispositivoAdmin(admin.ModelAdmin):
    list_display = (
        "nombre",
        "zona",
        "categoria",
        "consumo_kwh",
        "activo",
    )
    search_fields = (
        "nombre",
        "zona__nombre",
        "categoria__nombre",
    )
    list_filter = (
        "activo",
        "categoria",
        "zona__organizacion",
    )
    ordering = (
        "zona__nombre",
        "nombre",
    )
    list_select_related = (
        "zona",
        "categoria",
        "zona__organizacion",
    )


@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = (
        "usuario",
        "organizacion",
    )
    search_fields = (
        "usuario__username",
        "usuario__first_name",
        "usuario__last_name",
        "organizacion__nombre",
    )
    list_filter = (
        "organizacion",
    )
    ordering = (
        "usuario__username",
    )
    list_select_related = (
        "usuario",
        "organizacion",
    )