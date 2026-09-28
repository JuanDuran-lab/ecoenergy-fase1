"""
Scoping por organización.

Regla del proyecto:
- Un superusuario ve los registros de todas las organizaciones.
- Cualquier otro usuario ve solo los registros de la organización
  asignada en su perfil (accounts.UserProfile).
- Un usuario sin organización no ve nada.

Cada modelo con scoping declara el atributo `organization_lookup`, que
indica el camino ORM hacia la organización. Ejemplos:
    Zone.organization_lookup = "organization"
    Device.organization_lookup = "zone__organization"
"""

from django.core.exceptions import ObjectDoesNotExist


def get_user_organization(user):
    """Retorna la organización del usuario o None."""
    if user is None or not user.is_authenticated:
        return None

    try:
        return user.profile.organization
    except (AttributeError, ObjectDoesNotExist):
        return None


def user_has_global_scope(user):
    return bool(user and user.is_authenticated and user.is_superuser)


def scope_queryset(queryset, user):
    """Filtra un QuerySet según la organización del usuario."""
    if user_has_global_scope(user):
        return queryset

    organization = get_user_organization(user)
    if organization is None:
        return queryset.none()

    lookup = getattr(queryset.model, "organization_lookup", None)
    if lookup is None:
        # Modelo sin organización (tablas maestras compartidas).
        return queryset

    return queryset.filter(**{lookup: organization})


def object_in_user_scope(obj, user):
    """True si el objeto pertenece al ámbito del usuario."""
    return scope_queryset(
        type(obj)._default_manager.filter(pk=obj.pk), user
    ).exists()
