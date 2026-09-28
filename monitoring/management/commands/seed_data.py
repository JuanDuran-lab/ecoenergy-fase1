import os
from decimal import Decimal

from django.contrib.auth.models import Permission, User
from django.core.management.base import BaseCommand, CommandError

from accounts.models import UserProfile
from monitoring.models import (
    Category,
    Device,
    Organization,
    Zone,
    ZoneStatus,
    ZoneType,
)


def env_password(name):
    value = os.getenv(name)
    if not value:
        raise CommandError(
            f"Falta la variable de entorno {name}. Defínela en el archivo .env "
            "(ver .env.example)."
        )
    return value


class Command(BaseCommand):
    help = "Carga datos reproducibles de demostración para EcoEnergy."

    def handle(self, *args, **options):
        passwords = {
            "admin_demo": env_password("SEED_ADMIN_PASSWORD"),
            "operador_norte": env_password("SEED_SUPERVISOR_PASSWORD"),
            "operador_sur": env_password("SEED_READER_PASSWORD"),
        }

        north, _ = Organization.objects.update_or_create(
            tax_id="76.111.111-1", defaults={"name": "EcoEnergy Norte"}
        )
        south, _ = Organization.objects.update_or_create(
            tax_id="76.222.222-2", defaults={"name": "EcoEnergy Sur"}
        )

        hvac, _ = Category.objects.update_or_create(name="Climatización")
        lighting, _ = Category.objects.update_or_create(name="Iluminación")
        computing, _ = Category.objects.update_or_create(name="Computación")

        office, _ = ZoneType.objects.update_or_create(name="Oficina")
        warehouse, _ = ZoneType.objects.update_or_create(name="Bodega")
        tech_room, _ = ZoneType.objects.update_or_create(name="Sala técnica")

        operational, _ = ZoneStatus.objects.update_or_create(name="Operativa")
        maintenance, _ = ZoneStatus.objects.update_or_create(name="Mantenimiento")

        zones = {}
        for org, name, zone_type, status, limit in [
            (north, "Recepción", office, operational, "100.00"),
            (north, "Oficina administrativa", office, operational, "80.00"),
            (north, "Sala de servidores", tech_room, operational, "150.00"),
            (south, "Recepción", office, operational, "90.00"),
            (south, "Bodega principal", warehouse, maintenance, "60.00"),
        ]:
            zones[(org.pk, name)], _ = Zone.objects.update_or_create(
                organization=org,
                name=name,
                defaults={
                    "zone_type": zone_type,
                    "status": status,
                    "consumption_limit_kwh": Decimal(limit),
                },
            )

        for org, zone_name, category, name, consumption, active in [
            (north, "Recepción", hvac, "Aire acondicionado recepción", "45.00", True),
            (north, "Recepción", lighting, "Iluminación recepción", "25.00", True),
            (north, "Oficina administrativa", computing, "Estaciones de trabajo", "50.00", True),
            (north, "Sala de servidores", computing, "Servidor principal", "120.00", True),
            (north, "Sala de servidores", hvac, "Climatización servidores", "55.00", True),
            (south, "Recepción", lighting, "Iluminación recepción sur", "30.00", True),
            (south, "Bodega principal", lighting, "Iluminación bodega", "20.00", False),
        ]:
            Device.objects.update_or_create(
                zone=zones[(org.pk, zone_name)],
                name=name,
                defaults={
                    "category": category,
                    "nominal_consumption_kwh": Decimal(consumption),
                    "is_active": active,
                },
            )

        admin_user, _ = User.objects.get_or_create(username="admin_demo")
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.set_password(passwords["admin_demo"])
        admin_user.save()

        operator_permissions = Permission.objects.filter(
            content_type__app_label="monitoring",
            codename__in=[
                "view_zone",
                "add_zone",
                "change_zone",
                "view_device",
                "add_device",
                "change_device",
            ],
        )

        for username, organization in [("operador_norte", north), ("operador_sur", south)]:
            user, _ = User.objects.get_or_create(username=username)
            user.is_staff = True
            user.is_superuser = False
            user.set_password(passwords[username])
            user.save()
            user.user_permissions.set(operator_permissions)
            UserProfile.objects.update_or_create(
                user=user, defaults={"organization": organization}
            )

        self.stdout.write(self.style.SUCCESS("Datos de demostración cargados."))
