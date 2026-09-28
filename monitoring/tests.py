from decimal import Decimal

from django.contrib.auth.models import Permission, User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from accounts.models import UserProfile

from .models import Category, Device, Organization, Zone, ZoneStatus, ZoneType

TEST_PASSWORD = "Prueba#Segura2026"


class EcoEnergyBaseTest(TestCase):
    def setUp(self):
        self.org_north = Organization.objects.create(name="EcoEnergy Norte", tax_id="76.111.111-1")
        self.org_south = Organization.objects.create(name="EcoEnergy Sur", tax_id="76.222.222-2")
        self.category = Category.objects.create(name="Climatización")
        self.zone_type = ZoneType.objects.create(name="Oficina")
        self.zone_status = ZoneStatus.objects.create(name="Operativa")

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
            name="Aire acondicionado Norte",
            nominal_consumption_kwh=Decimal("45.00"),
        )
        self.device_south = Device.objects.create(
            zone=self.zone_south,
            category=self.category,
            name="Aire acondicionado Sur",
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
            name="Dispositivo inválido",
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

    def test_zone_soft_delete_cascades_to_devices(self):
        self.zone_north.soft_delete()
        self.assertFalse(Device.objects.filter(pk=self.device_north.pk).exists())

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
