"""
Resumen de los datos cargados, para la demostración.

Uso:
    python manage.py resumen_datos

Muestra, sin entrar al Admin:
- los 6 modelos de la API con su cantidad de registros (sin contar los
  eliminados lógicamente) y el total de registros de negocio;
- la distribución por organización;
- los usuarios con su rol web, rol API y organización (nunca contraseñas).
"""

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from api.permissions import API_ADMIN_GROUP, API_OPERATOR_GROUP
from monitoring.models import (
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

MINIMUM_RECORDS = 2000

API_MODELS = [
    ("Principal", "Zonas", Zone, "/api/zonas/"),
    ("Principal", "Dispositivos", Device, "/api/dispositivos/"),
    ("Principal", "Fabricantes", Manufacturer, "/api/fabricantes/"),
    ("Principal", "Categorías", Category, "/api/categorias/"),
    ("Operacional", "Lecturas", ConsumptionReading, "/api/lecturas/"),
    ("Operacional", "Alertas", Alert, "/api/alertas/"),
]
OTHER_MODELS = [
    ("Organizaciones", Organization),
    ("Tipos de zona", ZoneType),
    ("Estados de zona", ZoneStatus),
    ("Severidades", AlertSeverity),
]
API_ROLES = (API_ADMIN_GROUP, API_OPERATOR_GROUP)


class Command(BaseCommand):
    help = "Muestra las cantidades por modelo, el total de registros y los usuarios de prueba."

    def handle(self, *args, **options):
        self.print_models()
        self.print_organizations()
        self.print_users()

    def title(self, text):
        self.stdout.write("")
        self.stdout.write(self.style.MIGRATE_HEADING(text))

    def print_models(self):
        self.title("Modelos de la API")
        self.stdout.write(f"  {'Tipo':<12} {'Modelo':<34} {'Registros':>9}  Ruta")
        api_total = 0
        for kind, label, model, route in API_MODELS:
            count = model.objects.count()
            api_total += count
            name = f"{label} ({model.__name__})"
            self.stdout.write(f"  {kind:<12} {name:<34} {count:>9}  {route}")

        other_total = 0
        parts = []
        for label, model in OTHER_MODELS:
            count = model.objects.count()
            other_total += count
            parts.append(f"{label} {count}")
        self.stdout.write(f"  Otras tablas de negocio: {', '.join(parts)}")

        total = api_total + other_total
        deleted = sum(
            model.all_objects.filter(deleted_at__isnull=False).count()
            for model in [m for _, _, m, _ in API_MODELS] + [m for _, m in OTHER_MODELS]
        )
        status = (
            self.style.SUCCESS("cumple el mínimo de 2.000")
            if total >= MINIMUM_RECORDS
            else self.style.ERROR("bajo el mínimo de 2.000: ejecute seed_data --reset")
        )
        self.stdout.write(f"  TOTAL registros de negocio: {total} ({status})")
        if deleted:
            self.stdout.write(f"  Eliminados lógicamente (no se cuentan): {deleted}")

    def print_organizations(self):
        self.title("Por organización")
        for organization in Organization.objects.order_by("name"):
            zones = Zone.objects.filter(organization=organization).count()
            devices = Device.objects.filter(zone__organization=organization).count()
            readings = ConsumptionReading.objects.filter(
                device__zone__organization=organization
            ).count()
            alerts = Alert.objects.filter(zone__organization=organization).count()
            self.stdout.write(
                f"  {organization.name:<20} {zones:>3} zonas  {devices:>4} dispositivos  "
                f"{readings:>5} lecturas  {alerts:>4} alertas"
            )

    def print_users(self):
        self.title("Usuarios")
        self.stdout.write(
            f"  {'Usuario':<18} {'Activo':<7} {'Rol web':<30} {'Rol API':<20} Organización"
        )
        users = User.objects.prefetch_related("groups").select_related("profile__organization")
        for user in users.order_by("username"):
            groups = [group.name for group in user.groups.all()]
            web_roles = [name for name in groups if name not in API_ROLES]
            api_roles = [name for name in groups if name in API_ROLES]

            web_role = ", ".join(web_roles) or "-"
            if user.is_superuser:
                web_role += " (superusuario)"
                api_role = "Todo (superusuario)"
            else:
                api_role = ", ".join(api_roles) or "Sin rol API (403)"

            profile = getattr(user, "profile", None)
            organization = getattr(profile, "organization", None)
            if organization is None:
                organization = "Todas" if user.is_superuser else "-"

            self.stdout.write(
                f"  {user.username:<18} {'sí' if user.is_active else 'no':<7} "
                f"{web_role:<30} {api_role:<20} {organization}"
            )
        self.stdout.write("")
        self.stdout.write("  Las contraseñas no se muestran: están en el archivo .env (SEED_*).")
