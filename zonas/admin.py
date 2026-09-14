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


def obtener_organizacion_usuario(user):
    """
    Retorna la organización asociada al usuario.

    Los superusuarios no necesitan organización porque pueden
    acceder a todos los registros.
    """
    if user.is_superuser:
        return None

    try:
        return user.perfil_ecoenergy.organizacion
    except PerfilUsuario.DoesNotExist:
        return None


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


class DispositivoInline(admin.TabularInline):
    model = Dispositivo
    extra = 0
    fields = (
        "nombre",
        "categoria",
        "consumo_kwh",
        "activo",
    )


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

    inlines = (DispositivoInline,)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)

        if request.user.is_superuser:
            return queryset

        organizacion = obtener_organizacion_usuario(request.user)

        if organizacion is None:
            return queryset.none()

        return queryset.filter(
            organizacion=organizacion
        )

    def get_list_filter(self, request):
        if request.user.is_superuser:
            return (
                "organizacion",
                "tipo",
                "estado",
            )

        return (
            "tipo",
            "estado",
        )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if (
            db_field.name == "organizacion"
            and not request.user.is_superuser
        ):
            organizacion = obtener_organizacion_usuario(
                request.user
            )

            if organizacion is None:
                kwargs["queryset"] = Organizacion.objects.none()
            else:
                kwargs["queryset"] = Organizacion.objects.filter(
                    pk=organizacion.pk
                )

        return super().formfield_for_foreignkey(
            db_field,
            request,
            **kwargs,
        )

    def has_change_permission(self, request, obj=None):
        permiso = super().has_change_permission(
            request,
            obj,
        )

        if not permiso:
            return False

        if request.user.is_superuser or obj is None:
            return True

        organizacion = obtener_organizacion_usuario(
            request.user
        )

        return (
            organizacion is not None
            and obj.organizacion_id == organizacion.id
        )

    def has_delete_permission(self, request, obj=None):
        if not request.user.is_superuser:
            return False

        return super().has_delete_permission(
            request,
            obj,
        )


@admin.action(
    description="Desactivar dispositivos seleccionados"
)
def desactivar_dispositivos(modeladmin, request, queryset):
    actualizados = queryset.update(activo=False)

    modeladmin.message_user(
        request,
        (
            f"{actualizados} dispositivo(s) "
            "desactivado(s) correctamente."
        ),
    )


@admin.action(
    description="Activar dispositivos seleccionados"
)
def activar_dispositivos(modeladmin, request, queryset):
    actualizados = queryset.update(activo=True)

    modeladmin.message_user(
        request,
        (
            f"{actualizados} dispositivo(s) "
            "activado(s) correctamente."
        ),
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

    actions = (
        activar_dispositivos,
        desactivar_dispositivos,
    )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)

        if request.user.is_superuser:
            return queryset

        organizacion = obtener_organizacion_usuario(
            request.user
        )

        if organizacion is None:
            return queryset.none()

        return queryset.filter(
            zona__organizacion=organizacion
        )
    def get_list_filter(self, request):
        if request.user.is_superuser:
            return (
                "activo",
                "categoria",
                "zona__organizacion",
            )

        return (
            "activo",
            "categoria",
        )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if (
            db_field.name == "zona"
            and not request.user.is_superuser
        ):
            organizacion = obtener_organizacion_usuario(
                request.user
            )

            if organizacion is None:
                kwargs["queryset"] = Zona.objects.none()
            else:
                kwargs["queryset"] = Zona.objects.filter(
                    organizacion=organizacion
                )

        return super().formfield_for_foreignkey(
            db_field,
            request,
            **kwargs,
        )

    def has_change_permission(self, request, obj=None):
        permiso = super().has_change_permission(
            request,
            obj,
        )

        if not permiso:
            return False

        if request.user.is_superuser or obj is None:
            return True

        organizacion = obtener_organizacion_usuario(
            request.user
        )

        return (
            organizacion is not None
            and obj.zona.organizacion_id == organizacion.id
        )

    def has_delete_permission(self, request, obj=None):
        if not request.user.is_superuser:
            return False

        return super().has_delete_permission(
            request,
            obj,
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