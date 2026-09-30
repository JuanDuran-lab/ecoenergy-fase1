"""
Scoping por organización (regla de seguridad central del proyecto).

- Superusuario: ve los registros de todas las organizaciones.
- Otro usuario: solo ve la organización asignada en su perfil.
- Usuario sin organización: no ve nada.

Cada modelo declara `organization_lookup`, el camino ORM hacia su
organización (ej. Device -> "zone__organization"). Lo usan las vistas, los
formularios y el Admin.
"""

from django.core.exceptions import ObjectDoesNotExist


def get_user_organization(user):
    if user is None or not user.is_authenticated:
        return None

    try:
        return user.profile.organization
    except (AttributeError, ObjectDoesNotExist):
        return None


def user_has_global_scope(user):
    return bool(user and user.is_authenticated and user.is_superuser)


def scope_queryset(queryset, user):
    if user_has_global_scope(user):
        return queryset

    organization = get_user_organization(user)
    if organization is None:
        return queryset.none()

    lookup = getattr(queryset.model, "organization_lookup", None)
    if lookup is None:
        return queryset

    return queryset.filter(**{lookup: organization})


def object_in_user_scope(obj, user):
    return scope_queryset(
        type(obj)._default_manager.filter(pk=obj.pk), user
    ).exists()
