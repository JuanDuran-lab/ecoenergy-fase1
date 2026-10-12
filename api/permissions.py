"""
Permisos por rol de la API REST (/api/).

El rol API es el grupo del usuario:

    Rol                  GET (consultar)   POST / PUT / PATCH / DELETE
    Administrador API    sí                sí
    Operador API         sí                no -> 403
    Sin rol API          no -> 403         no -> 403

Una solicitud sin token (o con token inválido) no llega a este control: la
autenticación JWT la rechaza antes con 401. El scoping por organización se
aplica después, en las vistas (api/views.py).
"""

from rest_framework.permissions import SAFE_METHODS, BasePermission

API_ADMIN_GROUP = "Administrador API"
API_OPERATOR_GROUP = "Operador API"


class ApiRolePermission(BasePermission):
    message = "Tu usuario no tiene un rol API asignado."

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False

        if user.is_superuser:
            return True

        groups = set(user.groups.values_list("name", flat=True))
        if API_ADMIN_GROUP in groups:
            return True
        if API_OPERATOR_GROUP in groups:
            if request.method in SAFE_METHODS:
                return True
            self.message = "El rol Operador API solo permite consultar (GET)."
            return False
        return False
