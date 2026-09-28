"""
Clases base para el Django Admin.

- SoftDeleteAdmin: el Admin nunca elimina físicamente. Eliminar desde el
  Admin marca deleted_at, y un filtro permite ver/restaurar eliminados.
- OrganizationScopedAdminMixin: aplica el mismo scoping por organización
  que las vistas propias (core.scoping).
"""

from django.contrib import admin, messages

from .scoping import get_user_organization, scope_queryset


class DeletedStatusFilter(admin.SimpleListFilter):
    title = "estado del registro"
    parameter_name = "record_status"

    def lookups(self, request, model_admin):
        return (
            ("active", "Activos"),
            ("deleted", "Eliminados (lógico)"),
            ("all", "Todos"),
        )

    def choices(self, changelist):
        # Se oculta la opción "Todo" que agrega Django por defecto,
        # porque el valor por defecto de este filtro es "Activos".
        for lookup, title in self.lookup_choices:
            yield {
                "selected": (self.value() or "active") == lookup,
                "query_string": changelist.get_query_string(
                    {self.parameter_name: lookup}
                ),
                "display": title,
            }

    def queryset(self, request, queryset):
        value = self.value() or "active"
        if value == "active":
            return queryset.filter(deleted_at__isnull=True)
        if value == "deleted":
            return queryset.filter(deleted_at__isnull=False)
        return queryset


@admin.action(description="Eliminar (borrado lógico) los seleccionados")
def soft_delete_selected(modeladmin, request, queryset):
    if not modeladmin.has_delete_permission(request):
        modeladmin.message_user(
            request, "No tienes permiso para eliminar.", messages.ERROR
        )
        return
    count = queryset.delete()
    modeladmin.message_user(
        request, f"{count} registro(s) eliminado(s) lógicamente."
    )


@admin.action(description="Restaurar los seleccionados")
def restore_selected(modeladmin, request, queryset):
    if not modeladmin.has_delete_permission(request):
        modeladmin.message_user(
            request, "No tienes permiso para restaurar.", messages.ERROR
        )
        return
    count = queryset.restore()
    modeladmin.message_user(request, f"{count} registro(s) restaurado(s).")


class SoftDeleteAdmin(admin.ModelAdmin):
    actions = (soft_delete_selected, restore_selected)
    readonly_fields = ("created_at", "updated_at", "deleted_at")

    def get_queryset(self, request):
        # Se usa all_objects para que el filtro "Eliminados" funcione.
        queryset = self.model.all_objects.get_queryset()
        ordering = self.get_ordering(request)
        if ordering:
            queryset = queryset.order_by(*ordering)
        return queryset

    def get_list_filter(self, request):
        return (DeletedStatusFilter, *super().get_list_filter(request))

    def get_actions(self, request):
        actions = super().get_actions(request)
        # La acción estándar hace borrado físico: se reemplaza.
        actions.pop("delete_selected", None)
        return actions

    def delete_model(self, request, obj):
        obj.soft_delete()

    def delete_queryset(self, request, queryset):
        queryset.delete()

    def get_deleted_objects(self, objs, request):
        # Con borrado lógico no se eliminan objetos relacionados
        # físicamente, así que la confirmación solo lista el objeto.
        return [str(obj) for obj in objs], {}, set(), []


class OrganizationScopedAdminMixin:
    """
    Aplica core.scoping al Admin. `scoped_fk_fields` define qué FK del
    formulario se filtran por organización, por ejemplo {"zone": Zone}.
    """

    scoped_fk_fields = {}

    def get_queryset(self, request):
        return scope_queryset(super().get_queryset(request), request.user)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "organization" and not request.user.is_superuser:
            organization = get_user_organization(request.user)
            model = db_field.remote_field.model
            kwargs["queryset"] = (
                model.objects.filter(pk=organization.pk)
                if organization
                else model.objects.none()
            )
        elif db_field.name in self.scoped_fk_fields:
            model = self.scoped_fk_fields[db_field.name]
            kwargs["queryset"] = scope_queryset(
                model.objects.all(), request.user
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_list_filter(self, request):
        filters = super().get_list_filter(request)
        if request.user.is_superuser:
            return filters
        # Un usuario con scoping no necesita filtrar por organización.
        return tuple(
            f for f in filters
            if not (isinstance(f, str) and f.endswith("organization"))
        )
