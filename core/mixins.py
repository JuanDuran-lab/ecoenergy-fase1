"""
Controles de acceso de las vistas, en este orden:
1. Sin sesión                -> redirige al login.
2. Con sesión y sin permiso  -> HTTP 403.
3. Registro de otra organización -> HTTP 404 (scoping).
"""

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

from .scoping import scope_queryset


class ModelPermissionMixin(LoginRequiredMixin, PermissionRequiredMixin):
    permission_action = "view"

    def get_permission_required(self):
        if self.permission_required:
            return super().get_permission_required()
        opts = self.model._meta
        return (f"{opts.app_label}.{self.permission_action}_{opts.model_name}",)


class OrganizationScopedMixin:
    def get_queryset(self):
        return scope_queryset(super().get_queryset(), self.request.user)
