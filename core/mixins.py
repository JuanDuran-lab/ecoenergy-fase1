"""
Mixins reutilizables para las vistas basadas en clases.

Orden de seguridad en cada vista:
1. LoginRequiredMixin      -> sin sesión: redirige al login.
2. PermissionRequiredMixin -> con sesión pero sin permiso: HTTP 403.
3. OrganizationScopedMixin -> con permiso: solo ve/edita registros de su
                              organización. Un registro ajeno responde 404.
"""

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

from .scoping import scope_queryset


class ModelPermissionMixin(LoginRequiredMixin, PermissionRequiredMixin):
    """
    Deriva el permiso requerido desde el modelo de la vista.
    Ej.: model = Zone y permission_action = "change" -> "monitoring.change_zone".
    """

    permission_action = "view"

    def get_permission_required(self):
        if self.permission_required:
            return super().get_permission_required()
        opts = self.model._meta
        return (f"{opts.app_label}.{self.permission_action}_{opts.model_name}",)


class OrganizationScopedMixin:
    """Filtra get_queryset() por la organización del usuario."""

    def get_queryset(self):
        return scope_queryset(super().get_queryset(), self.request.user)
