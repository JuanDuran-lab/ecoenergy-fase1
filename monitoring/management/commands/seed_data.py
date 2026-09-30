import os
import random
from datetime import timedelta
from decimal import ROUND_HALF_UP, Decimal

from django.contrib.auth.models import Group, Permission, User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from accounts.models import UserProfile
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
from monitoring.queries import annotate_zone_metrics

RANDOM_SEED = 2026
ZONES_PER_ORGANIZATION = 8
DEVICES_PER_ZONE = 5
READINGS_PER_DEVICE = 10
READING_WINDOW_DAYS = 45

ORGANIZATIONS = [
    ("EcoEnergy Norte", "76.111.111-1"),
    ("EcoEnergy Sur", "76.222.222-2"),
    ("EcoEnergy Centro", "76.333.333-3"),
]

CATEGORIES = [
    ("Climatización", "Aire acondicionado, calefacción y ventilación."),
    ("Iluminación", "Luminarias interiores y exteriores."),
    ("Computación", "Servidores, estaciones de trabajo y redes."),
    ("Motores", "Bombas, compresores y motores industriales."),
    ("Refrigeración", "Cámaras de frío y refrigeradores."),
    ("Sensores", "Sensores de monitoreo y medición."),
]

ZONE_TYPES = [
    ("Oficina", "Espacios de trabajo administrativo."),
    ("Bodega", "Espacios de almacenamiento."),
    ("Sala técnica", "Espacios con equipamiento técnico."),
    ("Producción", "Áreas de proceso productivo."),
    ("Área común", "Pasillos, recepción y espacios compartidos."),
]

ZONE_STATUSES = [
    ("Operativa", "Zona en funcionamiento normal."),
    ("Mantenimiento", "Zona temporalmente en mantenimiento."),
    ("Inactiva", "Zona sin operación."),
]

MANUFACTURERS = [
    ("Schneider Electric", "Francia", "https://www.se.com"),
    ("Siemens", "Alemania", "https://www.siemens.com"),
    ("ABB", "Suiza", "https://new.abb.com"),
    ("Philips", "Países Bajos", "https://www.philips.com"),
    ("LG Electronics", "Corea del Sur", "https://www.lg.com"),
    ("Daikin", "Japón", "https://www.daikin.com"),
    ("Dell Technologies", "Estados Unidos", "https://www.dell.com"),
    ("WEG", "Brasil", "https://www.weg.net"),
]

SEVERITIES = [
    ("Baja", 1, "#198754", "Desviación menor sobre el consumo nominal."),
    ("Media", 2, "#0dcaf0", "Desviación moderada, revisar en la semana."),
    ("Alta", 3, "#fd7e14", "Desviación importante, revisar en el día."),
    ("Crítica", 4, "#dc3545", "Riesgo operacional, atender de inmediato."),
]

ZONE_NAMES = [
    ("Recepción", "Área común"),
    ("Oficina administrativa", "Oficina"),
    ("Sala de servidores", "Sala técnica"),
    ("Bodega principal", "Bodega"),
    ("Línea de producción A", "Producción"),
    ("Línea de producción B", "Producción"),
    ("Casino", "Área común"),
    ("Laboratorio", "Sala técnica"),
]

DEVICE_TEMPLATES = {
    "Climatización": ["Aire acondicionado", "Calefactor", "Ventilador industrial"],
    "Iluminación": ["Panel LED", "Foco halógeno", "Luminaria exterior"],
    "Computación": ["Servidor rack", "Estación de trabajo", "Switch de red"],
    "Motores": ["Bomba de agua", "Compresor", "Motor de cinta"],
    "Refrigeración": ["Cámara de frío", "Refrigerador", "Congelador"],
    "Sensores": ["Sensor de temperatura", "Medidor inteligente", "Sensor de humedad"],
}

NOMINAL_RANGES = {
    "Climatización": (20, 90),
    "Iluminación": (5, 30),
    "Computación": (10, 120),
    "Motores": (40, 200),
    "Refrigeración": (30, 150),
    "Sensores": (1, 5),
}

TWO_PLACES = Decimal("0.01")


def money(value):
    return Decimal(str(value)).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


class Command(BaseCommand):
    help = "Carga datos reproducibles de demostración (más de 1.000 registros)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Elimina físicamente los datos de negocio antes de cargar.",
        )

    def handle(self, *args, **options):
        users_config = self.read_users_config()

        if options["reset"]:
            self.reset_business_data()
        elif Zone.all_objects.exists():
            raise CommandError(
                "La base ya tiene datos. Usa 'python manage.py seed_data --reset' "
                "para borrarlos y volver a cargar."
            )

        self.random = random.Random(RANDOM_SEED)
        self.now = timezone.now()

        with transaction.atomic():
            organizations = self.create_organizations()
            masters = self.create_masters()
            zones = self.create_zones(organizations, masters)
            devices = self.create_devices(zones, masters)
            readings = self.create_readings(devices)
            alerts = self.create_alerts(readings, masters)
            self.calibrate_zone_limits()
            groups = self.create_groups()
            self.create_users(users_config, organizations, groups)

        self.print_summary(organizations, masters, zones, devices, readings, alerts)

    def read_users_config(self):
        config = [
            {
                "username": "admin_demo",
                "first_name": "Ana",
                "last_name": "Administradora",
                "email": os.getenv("SEED_ADMIN_EMAIL", "admin@ecoenergy.demo"),
                "password_var": "SEED_ADMIN_PASSWORD",
                "group": "Administrador",
                "organization": None,
                "is_staff": True,
                "is_superuser": True,
            },
            {
                "username": "supervisor_norte",
                "first_name": "Sergio",
                "last_name": "Supervisor",
                "email": os.getenv("SEED_SUPERVISOR_EMAIL", "supervisor@ecoenergy.demo"),
                "password_var": "SEED_SUPERVISOR_PASSWORD",
                "group": "Supervisor",
                "organization": "EcoEnergy Norte",
                "is_staff": True,
                "is_superuser": False,
            },
            {
                "username": "lector_sur",
                "first_name": "Laura",
                "last_name": "Lectora",
                "email": os.getenv("SEED_READER_EMAIL", "lector@ecoenergy.demo"),
                "password_var": "SEED_READER_PASSWORD",
                "group": "Lector",
                "organization": "EcoEnergy Sur",
                "is_staff": False,
                "is_superuser": False,
            },
        ]

        for item in config:
            password = os.getenv(item["password_var"])
            if not password:
                raise CommandError(
                    f"Falta la variable {item['password_var']} en el archivo .env "
                    "(ver .env.example)."
                )
            try:
                validate_password(password)
            except ValidationError as error:
                raise CommandError(
                    f"{item['password_var']} no cumple la política de contraseñas: "
                    + " ".join(error.messages)
                )
            item["password"] = password

        return config

    def reset_business_data(self):
        self.stdout.write("Eliminando datos de negocio existentes...")
        UserProfile.objects.filter(organization__isnull=False).update(organization=None)
        for model in (
            Alert,
            ConsumptionReading,
            Device,
            Zone,
            Organization,
            Category,
            ZoneType,
            ZoneStatus,
            Manufacturer,
            AlertSeverity,
        ):
            model.all_objects.all().hard_delete()

    def create_organizations(self):
        return [
            Organization.objects.create(name=name, tax_id=tax_id)
            for name, tax_id in ORGANIZATIONS
        ]

    def create_masters(self):
        return {
            "categories": {
                name: Category.objects.create(name=name, description=description)
                for name, description in CATEGORIES
            },
            "zone_types": {
                name: ZoneType.objects.create(name=name, description=description)
                for name, description in ZONE_TYPES
            },
            "zone_statuses": {
                name: ZoneStatus.objects.create(name=name, description=description)
                for name, description in ZONE_STATUSES
            },
            "manufacturers": [
                Manufacturer.objects.create(name=name, country=country, website=website)
                for name, country, website in MANUFACTURERS
            ],
            "severities": [
                AlertSeverity.objects.create(
                    name=name, level=level, color=color, description=description
                )
                for name, level, color, description in SEVERITIES
            ],
        }

    def create_zones(self, organizations, masters):
        statuses = masters["zone_statuses"]
        zones = []
        for organization in organizations:
            for zone_name, zone_type in ZONE_NAMES[:ZONES_PER_ORGANIZATION]:
                status = self.random.choices(
                    [statuses["Operativa"], statuses["Mantenimiento"], statuses["Inactiva"]],
                    weights=[80, 15, 5],
                )[0]
                zones.append(
                    Zone(
                        organization=organization,
                        zone_type=masters["zone_types"][zone_type],
                        status=status,
                        name=zone_name,
                        description=f"{zone_name} de {organization.name}.",
                        consumption_limit_kwh=money(self.random.randint(150, 900)),
                    )
                )
        return Zone.objects.bulk_create(zones)

    def create_devices(self, zones, masters):
        categories = list(masters["categories"].values())
        devices = []
        serial = 0
        for zone in zones:
            for position in range(1, DEVICES_PER_ZONE + 1):
                serial += 1
                category = self.random.choice(categories)
                low, high = NOMINAL_RANGES[category.name]
                base_name = self.random.choice(DEVICE_TEMPLATES[category.name])
                devices.append(
                    Device(
                        zone=zone,
                        category=category,
                        manufacturer=self.random.choice(masters["manufacturers"]),
                        name=f"{base_name} {position:02d}",
                        serial_number=f"EE-{zone.organization.tax_id[:2]}-{serial:05d}",
                        nominal_consumption_kwh=money(self.random.uniform(low, high)),
                        installed_on=(
                            self.now - timedelta(days=self.random.randint(60, 1500))
                        ).date(),
                        is_active=self.random.random() > 0.08,
                    )
                )
        return Device.objects.bulk_create(devices)

    def create_readings(self, devices):
        readings = []
        for device in devices:
            days = self.random.sample(range(1, READING_WINDOW_DAYS + 1), READINGS_PER_DEVICE)
            for day in sorted(days, reverse=True):
                if self.random.random() < 0.12:
                    factor = self.random.uniform(1.3, 1.9)
                else:
                    factor = self.random.uniform(0.55, 1.05)
                reading_at = (self.now - timedelta(days=day)).replace(
                    hour=self.random.randint(7, 21),
                    minute=self.random.choice([0, 15, 30, 45]),
                    second=0,
                    microsecond=0,
                )
                readings.append(
                    ConsumptionReading(
                        device=device,
                        reading_at=reading_at,
                        consumption_kwh=money(float(device.nominal_consumption_kwh) * factor),
                    )
                )
        return ConsumptionReading.objects.bulk_create(readings, batch_size=500)

    def create_alerts(self, readings, masters):
        severities = masters["severities"]
        alerts = []
        for reading in readings:
            nominal = reading.device.nominal_consumption_kwh
            ratio = reading.consumption_kwh / nominal
            if ratio < Decimal("1.3"):
                continue

            if ratio >= Decimal("1.8"):
                severity = severities[3]
            elif ratio >= Decimal("1.6"):
                severity = severities[2]
            elif ratio >= Decimal("1.45"):
                severity = severities[1]
            else:
                severity = severities[0]

            status = self.random.choices(
                [Alert.Status.OPEN, Alert.Status.IN_PROGRESS, Alert.Status.RESOLVED],
                weights=[35, 25, 40],
            )[0]
            resolved_at = None
            if status == Alert.Status.RESOLVED:
                resolved_at = min(
                    reading.reading_at + timedelta(hours=self.random.randint(1, 72)),
                    self.now,
                )

            alerts.append(
                Alert(
                    zone=reading.device.zone,
                    device=reading.device,
                    reading=reading,
                    severity=severity,
                    title=f"Consumo {int((ratio - 1) * 100)}% sobre lo nominal",
                    description=(
                        f"{reading.device.name} registró {reading.consumption_kwh} kWh "
                        f"(nominal {nominal} kWh)."
                    ),
                    status=status,
                    detected_at=reading.reading_at,
                    resolved_at=resolved_at,
                )
            )
        return Alert.objects.bulk_create(alerts, batch_size=500)

    def calibrate_zone_limits(self):
        zones = annotate_zone_metrics(Zone.objects.all())
        for zone in zones:
            factor = Decimal(str(self.random.uniform(0.75, 1.4)))
            zone.consumption_limit_kwh = max(
                money(zone.consumption_kwh * factor), Decimal("10.00")
            )
        Zone.objects.bulk_update(zones, ["consumption_limit_kwh"])

    def create_groups(self):
        operational = ["zone", "device", "consumptionreading", "alert"]
        masters = [
            "organization",
            "category",
            "zonetype",
            "zonestatus",
            "manufacturer",
            "alertseverity",
        ]

        def perms(codenames):
            found = Permission.objects.filter(
                content_type__app_label="monitoring", codename__in=codenames
            )
            if found.count() != len(set(codenames)):
                raise CommandError("Faltan permisos. Ejecuta primero 'python manage.py migrate'.")
            return found

        all_codenames = [
            f"{action}_{model}"
            for model in operational + masters
            for action in ("view", "add", "change", "delete")
        ] + ["export_consumptionreading"]

        supervisor_codenames = [
            f"{action}_{model}"
            for model in operational
            for action in ("view", "add", "change", "delete")
        ] + [f"view_{model}" for model in masters] + ["export_consumptionreading"]

        reader_codenames = [f"view_{model}" for model in operational] + [
            "export_consumptionreading"
        ]

        groups = {}
        for name, codenames in [
            ("Administrador", all_codenames),
            ("Supervisor", supervisor_codenames),
            ("Lector", reader_codenames),
        ]:
            group, _ = Group.objects.get_or_create(name=name)
            group.permissions.set(perms(codenames))
            groups[name] = group
        return groups

    def create_users(self, users_config, organizations, groups):
        organizations_by_name = {org.name: org for org in organizations}
        for item in users_config:
            user, _ = User.objects.get_or_create(username=item["username"])
            user.first_name = item["first_name"]
            user.last_name = item["last_name"]
            user.email = item["email"]
            user.is_staff = item["is_staff"]
            user.is_superuser = item["is_superuser"]
            user.is_active = True
            user.set_password(item["password"])
            user.save()
            user.user_permissions.clear()
            user.groups.set([groups[item["group"]]])

            organization = organizations_by_name.get(item["organization"])
            UserProfile.objects.update_or_create(
                user=user, defaults={"organization": organization}
            )

    def print_summary(self, organizations, masters, zones, devices, readings, alerts):
        master_total = len(organizations) + sum(
            len(value) for value in masters.values()
        )
        operational_total = len(zones) + len(devices) + len(readings) + len(alerts)

        self.stdout.write(self.style.SUCCESS("Datos de demostración cargados."))
        self.stdout.write(f"  Organizaciones:        {len(organizations)}")
        self.stdout.write(f"  Otras tablas maestras: {master_total - len(organizations)}")
        self.stdout.write(f"  Zonas:                 {len(zones)}")
        self.stdout.write(f"  Dispositivos:          {len(devices)}")
        self.stdout.write(f"  Lecturas de consumo:   {len(readings)}")
        self.stdout.write(f"  Alertas:               {len(alerts)}")
        self.stdout.write(
            self.style.SUCCESS(
                f"  TOTAL registros de negocio: {master_total + operational_total}"
            )
        )
        self.stdout.write("")
        self.stdout.write("Usuarios de prueba (contraseñas definidas en .env):")
        self.stdout.write("  admin_demo       -> Administrador, todas las organizaciones")
        self.stdout.write("  supervisor_norte -> Supervisor, EcoEnergy Norte")
        self.stdout.write("  lector_sur       -> Lector, EcoEnergy Sur")
