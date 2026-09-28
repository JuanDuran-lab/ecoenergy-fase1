from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import Permission, User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from accounts.models import UserProfile

from django.utils import timezone

from .models import (
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

TEST_PASSWORD = "Prueba#Segura2026"


class EcoEnergyBaseTest(TestCase):
    def setUp(self):
        self.org_north = Organization.objects.create(name="EcoEnergy Norte", tax_id="76.111.111-1")
        self.org_south = Organization.objects.create(name="EcoEnergy Sur", tax_id="76.222.222-2")
        self.category = Category.objects.create(name="Climatización")
        self.zone_type = ZoneType.objects.create(name="Oficina")
        self.zone_status = ZoneStatus.objects.create(name="Operativa")
        self.manufacturer = Manufacturer.objects.create(name="Genérico")
        self.severity = AlertSeverity.objects.create(name="Alta", level=3)

        self.zone_north = Zone.objects.create(
            organization=self.org_north,
            zone_type=self.zone_type,
            status=self.zone_status,
            name="Recepción Norte",
            consumption_limit_kwh=Decimal("100.00"),
        )
        self.zone_south = Zone.objects.create(
            organization=self.org_south,
            zone_type=self.zone_type,
            status=self.zone_status,
            name="Recepción Sur",
            consumption_limit_kwh=Decimal("90.00"),
        )
        self.device_north = Device.objects.create(
            zone=self.zone_north,
            category=self.category,
            manufacturer=self.manufacturer,
            name="Aire acondicionado Norte",
            serial_number="SN-0001",
            installed_on=date(2025, 1, 1),
            nominal_consumption_kwh=Decimal("45.00"),
        )
        self.device_south = Device.objects.create(
            zone=self.zone_south,
            category=self.category,
            manufacturer=self.manufacturer,
            name="Aire acondicionado Sur",
            serial_number="SN-0002",
            installed_on=date(2025, 1, 1),
            nominal_consumption_kwh=Decimal("30.00"),
        )

        self.operator_north = User.objects.create_user(
            username="operador_norte", password=TEST_PASSWORD, is_staff=True
        )
        UserProfile.objects.create(user=self.operator_north, organization=self.org_north)
        self.operator_north.user_permissions.set(
            Permission.objects.filter(
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
        )


class ModelValidationTests(EcoEnergyBaseTest):
    def test_zone_rejects_zero_limit(self):
        zone = Zone(
            organization=self.org_north,
            zone_type=self.zone_type,
            status=self.zone_status,
            name="Zona inválida",
            consumption_limit_kwh=Decimal("0.00"),
        )
        with self.assertRaises(ValidationError):
            zone.full_clean()

    def test_device_rejects_negative_consumption(self):
        device = Device(
            zone=self.zone_north,
            category=self.category,
            manufacturer=self.manufacturer,
            name="Dispositivo inválido",
            serial_number="SN-0003",
            installed_on=date(2025, 1, 1),
            nominal_consumption_kwh=Decimal("-1.00"),
        )
        with self.assertRaises(ValidationError):
            device.full_clean()

    def test_duplicate_zone_name_in_same_organization_is_rejected(self):
        zone = Zone(
            organization=self.org_north,
            zone_type=self.zone_type,
            status=self.zone_status,
            name="Recepción Norte",
            consumption_limit_kwh=Decimal("10.00"),
        )
        with self.assertRaises(ValidationError):
            zone.full_clean()


    def test_device_rejects_future_installation_date(self):
        self.device_north.installed_on = timezone.localdate() + timedelta(days=1)
        with self.assertRaises(ValidationError):
            self.device_north.full_clean()

    def test_reading_rejects_future_date(self):
        reading = ConsumptionReading(
            device=self.device_north,
            reading_at=timezone.now() + timedelta(hours=1),
            consumption_kwh=Decimal("10.00"),
        )
        with self.assertRaises(ValidationError):
            reading.full_clean()

    def test_reading_rejects_inactive_device(self):
        self.device_north.is_active = False
        self.device_north.save()
        reading = ConsumptionReading(
            device=self.device_north,
            reading_at=timezone.now(),
            consumption_kwh=Decimal("10.00"),
        )
        with self.assertRaises(ValidationError):
            reading.full_clean()

    def test_alert_device_must_belong_to_zone(self):
        alert = Alert(
            zone=self.zone_north,
            device=self.device_south,
            severity=self.severity,
            title="Consumo alto",
            detected_at=timezone.now(),
        )
        with self.assertRaises(ValidationError):
            alert.full_clean()

    def test_resolved_alert_requires_resolution_date(self):
        alert = Alert(
            zone=self.zone_north,
            severity=self.severity,
            title="Consumo alto",
            status=Alert.Status.RESOLVED,
            detected_at=timezone.now(),
        )
        with self.assertRaises(ValidationError):
            alert.full_clean()


class SoftDeleteTests(EcoEnergyBaseTest):
    def test_soft_delete_hides_record_but_keeps_row(self):
        self.device_north.soft_delete()

        self.assertFalse(Device.objects.filter(pk=self.device_north.pk).exists())
        self.assertTrue(Device.all_objects.filter(pk=self.device_north.pk).exists())

    def test_instance_delete_is_logical(self):
        self.device_north.delete()
        self.assertIsNotNone(Device.all_objects.get(pk=self.device_north.pk).deleted_at)

    def test_queryset_delete_is_logical(self):
        Device.objects.filter(zone=self.zone_north).delete()
        self.assertEqual(Device.all_objects.filter(zone=self.zone_north).count(), 1)
        self.assertEqual(Device.objects.filter(zone=self.zone_north).count(), 0)

    def test_zone_soft_delete_cascades_to_devices_readings_and_alerts(self):
        reading = ConsumptionReading.objects.create(
            device=self.device_north,
            reading_at=timezone.now(),
            consumption_kwh=Decimal("10.00"),
        )
        alert = Alert.objects.create(
            zone=self.zone_north,
            severity=self.severity,
            title="Consumo alto",
            detected_at=timezone.now(),
        )
        self.zone_north.soft_delete()
        self.assertFalse(Device.objects.filter(pk=self.device_north.pk).exists())
        self.assertFalse(ConsumptionReading.objects.filter(pk=reading.pk).exists())
        self.assertFalse(Alert.objects.filter(pk=alert.pk).exists())

    def test_deleted_name_can_be_reused(self):
        self.zone_north.soft_delete()
        zone = Zone(
            organization=self.org_north,
            zone_type=self.zone_type,
            status=self.zone_status,
            name="Recepción Norte",
            consumption_limit_kwh=Decimal("10.00"),
        )
        zone.full_clean()
        zone.save()


class AdminScopingTests(EcoEnergyBaseTest):
    def setUp(self):
        super().setUp()
        self.client.login(username="operador_norte", password=TEST_PASSWORD)

    def test_operator_sees_only_own_zones(self):
        response = self.client.get(reverse("admin:monitoring_zone_changelist"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Recepción Norte")
        self.assertNotContains(response, "Recepción Sur")

    def test_operator_sees_only_own_devices(self):
        response = self.client.get(reverse("admin:monitoring_device_changelist"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Aire acondicionado Norte")
        self.assertNotContains(response, "Aire acondicionado Sur")

    def test_operator_cannot_open_other_organization_zone(self):
        response = self.client.get(
            reverse("admin:monitoring_zone_change", args=[self.zone_south.pk])
        )
        self.assertEqual(response.status_code, 302)

    def test_admin_changelist_hides_soft_deleted(self):
        self.device_north.soft_delete()
        response = self.client.get(reverse("admin:monitoring_device_changelist"))
        self.assertNotContains(response, "Aire acondicionado Norte")


class SeedCommandTests(TestCase):
    ENV = {
        "SEED_ADMIN_PASSWORD": "Admin#Prueba2026",
        "SEED_SUPERVISOR_PASSWORD": "Super#Prueba2026",
        "SEED_READER_PASSWORD": "Lector#Prueba2026",
    }

    def test_seed_creates_more_than_1000_records_and_three_roles(self):
        from io import StringIO
        from unittest import mock

        from django.core.management import call_command

        with mock.patch.dict("os.environ", self.ENV):
            call_command("seed_data", stdout=StringIO())

        total = sum(
            model.objects.count()
            for model in (
                Organization,
                Category,
                ZoneType,
                ZoneStatus,
                Manufacturer,
                AlertSeverity,
                Zone,
                Device,
                ConsumptionReading,
                Alert,
            )
        )
        self.assertGreaterEqual(total, 1000)
        self.assertEqual(
            {
                user.username: user.groups.get().name
                for user in User.objects.filter(
                    username__in=["admin_demo", "supervisor_norte", "lector_sur"]
                )
            },
            {
                "admin_demo": "Administrador",
                "supervisor_norte": "Supervisor",
                "lector_sur": "Lector",
            },
        )
        self.assertTrue(
            User.objects.get(username="lector_sur").check_password(self.ENV["SEED_READER_PASSWORD"])
        )

    def test_seed_rejects_weak_password(self):
        from io import StringIO
        from unittest import mock

        from django.core.management import CommandError, call_command

        env = dict(self.ENV, SEED_READER_PASSWORD="corta")
        with mock.patch.dict("os.environ", env):
            with self.assertRaises(CommandError):
                call_command("seed_data", stdout=StringIO())


class ViewPermissionAndScopingTests(EcoEnergyBaseTest):
    def setUp(self):
        super().setUp()
        self.no_perms = User.objects.create_user("sin_permisos", password=TEST_PASSWORD)
        UserProfile.objects.create(user=self.no_perms, organization=self.org_north)
        self.admin = User.objects.create_superuser("admin", "admin@test.cl", TEST_PASSWORD)

    def login(self, username):
        self.client.login(username=username, password=TEST_PASSWORD)

    def test_anonymous_is_redirected_to_login(self):
        response = self.client.get(reverse("monitoring:zone_list"))
        self.assertEqual(response.status_code, 302)

    def test_user_without_permission_gets_403(self):
        self.login("sin_permisos")
        response = self.client.get(reverse("monitoring:zone_list"))
        self.assertEqual(response.status_code, 403)

    def test_zone_list_is_scoped_to_organization(self):
        self.login("operador_norte")
        response = self.client.get(reverse("monitoring:zone_list"))
        self.assertContains(response, "Recepción Norte")
        self.assertNotContains(response, "Recepción Sur")

    def test_other_organization_zone_returns_404(self):
        self.login("operador_norte")
        response = self.client.get(reverse("monitoring:zone_detail", args=[self.zone_south.pk]))
        self.assertEqual(response.status_code, 404)

    def test_superuser_sees_all_organizations(self):
        self.login("admin")
        response = self.client.get(reverse("monitoring:zone_list"))
        self.assertContains(response, "Recepción Norte")
        self.assertContains(response, "Recepción Sur")

    def test_summary_is_scoped(self):
        self.login("operador_norte")
        response = self.client.get(reverse("monitoring:zone_summary"))
        self.assertContains(response, "Recepción Norte")
        self.assertNotContains(response, "Recepción Sur")

    def test_soft_deleted_zone_not_listed(self):
        self.zone_north.soft_delete()
        self.login("operador_norte")
        response = self.client.get(reverse("monitoring:zone_list"))
        self.assertNotContains(response, "Recepción Norte")

    def test_zone_metrics_ignore_soft_deleted_readings(self):
        reading = ConsumptionReading.objects.create(
            device=self.device_north,
            reading_at=timezone.now() - timedelta(days=1),
            consumption_kwh=Decimal("500.00"),
        )
        reading.soft_delete()
        self.login("operador_norte")
        response = self.client.get(reverse("monitoring:zone_detail", args=[self.zone_north.pk]))
        self.assertEqual(response.context["zone"].consumption_kwh, Decimal("0.00"))

    def test_dashboard_counts_are_scoped(self):
        self.login("operador_norte")
        response = self.client.get(reverse("monitoring:dashboard"))
        stats = {stat["label"]: stat["value"] for stat in response.context["stats"]}
        self.assertEqual(stats["Zonas"], 1)
        self.assertEqual(stats["Dispositivos"], 1)


def make_image_file(name="foto.png", image_format="PNG", size=(40, 40)):
    from io import BytesIO

    from django.core.files.uploadedfile import SimpleUploadedFile
    from PIL import Image

    buffer = BytesIO()
    Image.new("RGB", size, (20, 120, 60)).save(buffer, format=image_format)
    return SimpleUploadedFile(name, buffer.getvalue(), content_type=f"image/{image_format.lower()}")


class CrudTests(EcoEnergyBaseTest):
    def setUp(self):
        super().setUp()
        import shutil
        import tempfile

        from django.test import override_settings

        self.media_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.media_dir, ignore_errors=True)
        media_override = override_settings(MEDIA_ROOT=self.media_dir)
        media_override.enable()
        self.addCleanup(media_override.disable)

        self.operator_north.user_permissions.add(
            *Permission.objects.filter(
                content_type__app_label="monitoring",
                codename__in=[
                    "view_consumptionreading",
                    "add_consumptionreading",
                    "change_consumptionreading",
                    "view_alert",
                    "add_alert",
                    "change_alert",
                ],
            )
        )
        self.reader = User.objects.create_user("lector", password=TEST_PASSWORD)
        UserProfile.objects.create(user=self.reader, organization=self.org_north)
        self.reader.user_permissions.set(
            Permission.objects.filter(
                content_type__app_label="monitoring", codename__in=["view_zone", "view_device"]
            )
        )
        self.client.login(username="operador_norte", password=TEST_PASSWORD)

    def zone_data(self, **overrides):
        data = {
            "name": "Bodega nueva",
            "zone_type": self.zone_type.pk,
            "status": self.zone_status.pk,
            "consumption_limit_kwh": "250.00",
            "description": "",
        }
        data.update(overrides)
        return data

    def device_data(self, **overrides):
        data = {
            "zone": self.zone_north.pk,
            "name": "Compresor 01",
            "serial_number": "ee-76-99999",
            "category": self.category.pk,
            "manufacturer": self.manufacturer.pk,
            "nominal_consumption_kwh": "40.00",
            "installed_on": "2025-06-01",
            "is_active": "on",
        }
        data.update(overrides)
        return data

    # Zonas ---------------------------------------------------------------

    def test_create_zone_assigns_user_organization(self):
        response = self.client.post(reverse("monitoring:zone_create"), self.zone_data())
        zone = Zone.objects.get(name="Bodega nueva")
        self.assertRedirects(response, zone.get_absolute_url())
        self.assertEqual(zone.organization, self.org_north)

    def test_create_zone_rejects_duplicate_name_case_insensitive(self):
        response = self.client.post(
            reverse("monitoring:zone_create"), self.zone_data(name="recepción norte")
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ya existe una zona con este nombre")

    def test_create_zone_rejects_zero_limit(self):
        response = self.client.post(
            reverse("monitoring:zone_create"), self.zone_data(consumption_limit_kwh="0")
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Zone.objects.filter(name="Bodega nueva").exists())

    def test_update_zone(self):
        response = self.client.post(
            reverse("monitoring:zone_update", args=[self.zone_north.pk]),
            self.zone_data(name="Recepción renovada"),
        )
        self.assertEqual(response.status_code, 302)
        self.zone_north.refresh_from_db()
        self.assertEqual(self.zone_north.name, "Recepción renovada")

    def test_cannot_update_other_organization_zone(self):
        response = self.client.post(
            reverse("monitoring:zone_update", args=[self.zone_south.pk]), self.zone_data()
        )
        self.assertEqual(response.status_code, 404)

    def test_reader_cannot_create_zone(self):
        self.client.login(username="lector", password=TEST_PASSWORD)
        response = self.client.get(reverse("monitoring:zone_create"))
        self.assertEqual(response.status_code, 403)

    # Dispositivos + imagen -----------------------------------------------

    def test_create_device_with_valid_image(self):
        data = self.device_data()
        data["image"] = make_image_file()
        response = self.client.post(reverse("monitoring:device_create"), data)
        device = Device.objects.get(serial_number="EE-76-99999")
        self.assertRedirects(response, device.get_absolute_url())
        self.assertTrue(device.image.name.startswith("devices/"))

    def test_rejects_fake_image_content(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        data = self.device_data()
        data["image"] = SimpleUploadedFile("virus.png", b"esto no es una imagen", "image/png")
        response = self.client.post(reverse("monitoring:device_create"), data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Device.objects.filter(serial_number="EE-76-99999").exists())

    def test_rejects_disallowed_extension(self):
        data = self.device_data()
        data["image"] = make_image_file(name="foto.gif", image_format="GIF")
        response = self.client.post(reverse("monitoring:device_create"), data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Device.objects.filter(serial_number="EE-76-99999").exists())

    def test_rejects_image_over_size_limit(self):
        from unittest import mock

        data = self.device_data()
        data["image"] = make_image_file()
        with mock.patch("monitoring.validators.MAX_IMAGE_SIZE", 10):
            response = self.client.post(reverse("monitoring:device_create"), data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "El máximo permitido")

    def test_rejects_duplicate_serial_number(self):
        response = self.client.post(
            reverse("monitoring:device_create"), self.device_data(serial_number="SN-0002")
        )
        self.assertContains(response, "Ya existe un dispositivo con este número de serie")

    def test_cannot_create_device_in_other_organization_zone(self):
        response = self.client.post(
            reverse("monitoring:device_create"), self.device_data(zone=self.zone_south.pk)
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Device.objects.filter(serial_number="EE-76-99999").exists())

    # Lecturas --------------------------------------------------------------

    def reading_data(self, **overrides):
        data = {
            "device": self.device_north.pk,
            "reading_at": (timezone.localtime() - timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M"),
            "consumption_kwh": "40.00",
            "notes": "",
        }
        data.update(overrides)
        return data

    def test_create_reading(self):
        response = self.client.post(reverse("monitoring:reading_create"), self.reading_data())
        self.assertEqual(response.status_code, 302)
        self.assertEqual(ConsumptionReading.objects.count(), 1)

    def test_reading_rejects_anomalous_value(self):
        response = self.client.post(
            reverse("monitoring:reading_create"), self.reading_data(consumption_kwh="500.00")
        )
        self.assertContains(response, "Valor anómalo")

    def test_reading_rejects_duplicate_datetime(self):
        self.client.post(reverse("monitoring:reading_create"), self.reading_data())
        response = self.client.post(reverse("monitoring:reading_create"), self.reading_data())
        self.assertContains(response, "Ya existe una lectura de este dispositivo")

    def test_reading_rejects_other_organization_device(self):
        response = self.client.post(
            reverse("monitoring:reading_create"), self.reading_data(device=self.device_south.pk)
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ConsumptionReading.objects.count(), 0)

    # Alertas ---------------------------------------------------------------

    def alert_data(self, **overrides):
        data = {
            "zone": self.zone_north.pk,
            "device": self.device_north.pk,
            "severity": self.severity.pk,
            "title": "Consumo elevado",
            "status": "open",
            "detected_at": (timezone.localtime() - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M"),
            "resolved_at": "",
            "description": "",
        }
        data.update(overrides)
        return data

    def test_create_alert(self):
        response = self.client.post(reverse("monitoring:alert_create"), self.alert_data())
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Alert.objects.count(), 1)

    def test_alert_resolved_requires_date(self):
        response = self.client.post(
            reverse("monitoring:alert_create"), self.alert_data(status="resolved")
        )
        self.assertContains(response, "debe indicar la fecha de resolución")

    def test_alert_rejects_device_from_other_zone(self):
        other_zone = Zone.objects.create(
            organization=self.org_north,
            zone_type=self.zone_type,
            status=self.zone_status,
            name="Bodega Norte",
            consumption_limit_kwh=Decimal("50.00"),
        )
        response = self.client.post(
            reverse("monitoring:alert_create"), self.alert_data(zone=other_zone.pk)
        )
        self.assertContains(response, "no pertenece a la zona")
