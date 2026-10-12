"""
Pruebas de la API REST: JWT (obtener y renovar), 401 sin token, 403 por rol,
CRUD de los cuatro modelos principales, solo lectura de los operacionales,
validaciones (400), id inexistente (404), scoping por organización,
borrado lógico (204) y paginación.
"""

from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import Group, User
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

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

from .permissions import API_ADMIN_GROUP, API_OPERATOR_GROUP

PASSWORD = "Prueba#Segura2026"
API = "/api"


class ApiBaseTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.org_north = Organization.objects.create(name="EcoEnergy Norte", tax_id="76.111.111-1")
        cls.org_south = Organization.objects.create(name="EcoEnergy Sur", tax_id="76.222.222-2")
        cls.category = Category.objects.create(name="Climatización")
        cls.manufacturer = Manufacturer.objects.create(name="Genérico")
        cls.zone_type = ZoneType.objects.create(name="Oficina")
        cls.zone_status = ZoneStatus.objects.create(name="Operativa")
        cls.severity = AlertSeverity.objects.create(name="Alta", level=3)

        cls.zone_north = cls.make_zone(cls.org_north, "Recepción Norte")
        cls.zone_south = cls.make_zone(cls.org_south, "Recepción Sur")
        cls.device_north = cls.make_device(cls.zone_north, "Aire Norte", "SN-0001")
        cls.device_south = cls.make_device(cls.zone_south, "Aire Sur", "SN-0002")

        now = timezone.now()
        ConsumptionReading.objects.bulk_create(
            ConsumptionReading(
                device=cls.device_south,
                reading_at=now - timedelta(hours=hour),
                consumption_kwh=Decimal("20.00"),
            )
            for hour in range(1, 26)
        )
        cls.reading_north = ConsumptionReading.objects.create(
            device=cls.device_north,
            reading_at=now - timedelta(hours=1),
            consumption_kwh=Decimal("80.00"),
        )
        cls.alert_north = Alert.objects.create(
            zone=cls.zone_north,
            device=cls.device_north,
            reading=cls.reading_north,
            severity=cls.severity,
            title="Consumo alto",
            detected_at=cls.reading_north.reading_at,
        )
        cls.alert_south = Alert.objects.create(
            zone=cls.zone_south,
            device=cls.device_south,
            severity=cls.severity,
            title="Consumo alto Sur",
            detected_at=now - timedelta(hours=2),
        )

        admin_group = Group.objects.create(name=API_ADMIN_GROUP)
        operator_group = Group.objects.create(name=API_OPERATOR_GROUP)
        cls.api_admin = cls.make_user("admin_api_norte", cls.org_north, admin_group)
        cls.operator = cls.make_user("operador_api_sur", cls.org_south, operator_group)
        cls.guest = cls.make_user("invitado", cls.org_north, None)

    @classmethod
    def make_zone(cls, organization, name):
        return Zone.objects.create(
            organization=organization,
            zone_type=cls.zone_type,
            status=cls.zone_status,
            name=name,
            consumption_limit_kwh=Decimal("100.00"),
        )

    @classmethod
    def make_device(cls, zone, name, serial):
        return Device.objects.create(
            zone=zone,
            category=cls.category,
            manufacturer=cls.manufacturer,
            name=name,
            serial_number=serial,
            installed_on=date(2025, 1, 1),
            nominal_consumption_kwh=Decimal("45.00"),
        )

    @classmethod
    def make_user(cls, username, organization, group):
        user = User.objects.create_user(username=username, password=PASSWORD)
        UserProfile.objects.create(user=user, organization=organization)
        if group is not None:
            user.groups.add(group)
        return user

    def obtain_tokens(self, user):
        response = self.client.post(
            f"{API}/token/",
            {"username": user.username, "password": PASSWORD},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return response.json()

    def authenticate(self, user):
        access = self.obtain_tokens(user)["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

    def device_payload(self, **overrides):
        payload = {
            "zone": self.zone_north.pk,
            "name": "Medidor nuevo",
            "serial_number": "EE-API-0001",
            "category": self.category.pk,
            "manufacturer": self.manufacturer.pk,
            "nominal_consumption_kwh": "12.50",
            "installed_on": "2026-01-15",
            "is_active": True,
        }
        payload.update(overrides)
        return payload


class JwtTests(ApiBaseTest):
    def test_obtain_and_refresh_token(self):
        tokens = self.obtain_tokens(self.api_admin)
        self.assertIn("access", tokens)
        self.assertIn("refresh", tokens)

        response = self.client.post(
            f"{API}/token/refresh/", {"refresh": tokens["refresh"]}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.json())

    def test_wrong_password_returns_401(self):
        response = self.client.post(
            f"{API}/token/",
            {"username": self.api_admin.username, "password": "incorrecta"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_without_token_returns_401_on_every_resource(self):
        for resource in ("zonas", "dispositivos", "fabricantes", "categorias", "lecturas", "alertas"):
            with self.subTest(resource=resource):
                response = self.client.get(f"{API}/{resource}/")
                self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invalid_token_returns_401(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer token-falso")
        response = self.client.get(f"{API}/zonas/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class RolePermissionTests(ApiBaseTest):
    def test_operator_can_read_but_not_write(self):
        self.authenticate(self.operator)
        self.assertEqual(self.client.get(f"{API}/zonas/").status_code, status.HTTP_200_OK)
        response = self.client.post(
            f"{API}/fabricantes/", {"name": "Nuevo"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(Manufacturer.objects.filter(name="Nuevo").exists())

    def test_operator_cannot_update_or_delete(self):
        self.authenticate(self.operator)
        url = f"{API}/zonas/{self.zone_south.pk}/"
        self.assertEqual(
            self.client.patch(url, {"description": "x"}, format="json").status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.assertEqual(self.client.delete(url).status_code, status.HTTP_403_FORBIDDEN)

    def test_user_without_api_role_gets_403(self):
        self.authenticate(self.guest)
        for resource in ("zonas", "dispositivos", "fabricantes", "categorias", "lecturas", "alertas"):
            with self.subTest(resource=resource):
                response = self.client.get(f"{API}/{resource}/")
                self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_operational_resources_are_read_only_for_admin(self):
        self.authenticate(self.api_admin)
        response = self.client.post(f"{API}/lecturas/", {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        response = self.client.delete(f"{API}/alertas/{self.alert_north.pk}/")
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class CrudTests(ApiBaseTest):
    def setUp(self):
        self.authenticate(self.api_admin)

    def test_device_full_crud_with_soft_delete(self):
        response = self.client.post(f"{API}/dispositivos/", self.device_payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        device_id = response.json()["id"]
        url = f"{API}/dispositivos/{device_id}/"

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["organization"], self.org_north.pk)

        response = self.client.patch(url, {"nominal_consumption_kwh": "15.00"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["nominal_consumption_kwh"], "15.00")

        response = self.client.put(url, self.device_payload(name="Medidor editado"), format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["name"], "Medidor editado")

        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(self.client.get(url).status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Device.all_objects.get(pk=device_id).is_deleted)

    def test_zone_created_in_user_organization(self):
        response = self.client.post(
            f"{API}/zonas/",
            {
                "name": "Bodega API",
                "zone_type": self.zone_type.pk,
                "status": self.zone_status.pk,
                "consumption_limit_kwh": "150.00",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()["organization"], self.org_north.pk)

    def test_zone_delete_cascades_soft_delete(self):
        response = self.client.delete(f"{API}/zonas/{self.zone_north.pk}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Device.objects.filter(pk=self.device_north.pk).exists())
        self.assertFalse(Alert.objects.filter(pk=self.alert_north.pk).exists())

    def test_catalog_crud(self):
        response = self.client.post(f"{API}/categorias/", {"name": "Bombas de calor"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        url = f"{API}/categorias/{response.json()['id']}/"
        self.assertEqual(self.client.get(url).status_code, status.HTTP_200_OK)
        response = self.client.patch(url, {"is_active": False}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.delete(url).status_code, status.HTTP_204_NO_CONTENT)

    def test_catalog_in_use_cannot_be_deleted(self):
        response = self.client.delete(f"{API}/fabricantes/{self.manufacturer.pk}/")
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertTrue(Manufacturer.objects.filter(pk=self.manufacturer.pk).exists())

    def test_operational_list_and_detail(self):
        response = self.client.get(f"{API}/lecturas/{self.reading_north.pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["device"], self.device_north.pk)
        response = self.client.get(f"{API}/alertas/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([a["id"] for a in response.json()["results"]], [self.alert_north.pk])


class ValidationTests(ApiBaseTest):
    def setUp(self):
        self.authenticate(self.api_admin)

    def test_field_validation_serial_number_format(self):
        response = self.client.post(
            f"{API}/dispositivos/", self.device_payload(serial_number="sn 1"), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("serial_number", response.json())

    def test_field_validation_future_installation_date(self):
        future = (timezone.localdate() + timedelta(days=5)).isoformat()
        response = self.client.post(
            f"{API}/dispositivos/", self.device_payload(installed_on=future), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("installed_on", response.json())

    def test_relation_validation_zone_from_other_organization(self):
        response = self.client.post(
            f"{API}/dispositivos/",
            self.device_payload(zone=self.zone_south.pk),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("zone", response.json())
        self.assertFalse(Device.objects.filter(serial_number="EE-API-0001").exists())

    def test_business_rule_duplicate_serial_number(self):
        response = self.client.post(
            f"{API}/dispositivos/",
            self.device_payload(serial_number=self.device_south.serial_number),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()["serial_number"],
            ["Ya existe un dispositivo con este número de serie."],
        )

    def test_inactive_category_rejected(self):
        inactive = Category.objects.create(name="Antigua", is_active=False)
        response = self.client.post(
            f"{API}/dispositivos/", self.device_payload(category=inactive.pk), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("category", response.json())

    def test_nonexistent_id_returns_404(self):
        response = self.client.get(f"{API}/zonas/999999/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("detail", response.json())


class ScopingTests(ApiBaseTest):
    def test_admin_only_sees_own_organization(self):
        self.authenticate(self.api_admin)
        response = self.client.get(f"{API}/zonas/")
        self.assertEqual([z["id"] for z in response.json()["results"]], [self.zone_north.pk])
        response = self.client.get(f"{API}/lecturas/")
        self.assertEqual(response.json()["count"], 1)

    def test_other_organization_record_returns_404(self):
        self.authenticate(self.api_admin)
        url = f"{API}/zonas/{self.zone_south.pk}/"
        self.assertEqual(self.client.get(url).status_code, status.HTTP_404_NOT_FOUND)
        response = self.client.patch(url, {"description": "x"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(self.client.delete(url).status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(Zone.all_objects.get(pk=self.zone_south.pk).is_deleted)

    def test_cannot_create_zone_in_other_organization(self):
        self.authenticate(self.api_admin)
        response = self.client.post(
            f"{API}/zonas/",
            {
                "organization": self.org_south.pk,
                "name": "Zona ajena",
                "zone_type": self.zone_type.pk,
                "status": self.zone_status.pk,
                "consumption_limit_kwh": "50.00",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("organization", response.json())


class PaginationTests(ApiBaseTest):
    def test_two_pages_return_different_results(self):
        self.authenticate(self.operator)
        first = self.client.get(f"{API}/lecturas/")
        second = self.client.get(f"{API}/lecturas/", {"page": 2})
        self.assertEqual(first.status_code, status.HTTP_200_OK)
        self.assertEqual(second.status_code, status.HTTP_200_OK)

        first_data, second_data = first.json(), second.json()
        self.assertEqual(first_data["count"], 25)
        self.assertEqual(first_data["total_pages"], 2)
        self.assertEqual(len(first_data["results"]), 20)
        self.assertEqual(len(second_data["results"]), 5)
        first_ids = {r["id"] for r in first_data["results"]}
        second_ids = {r["id"] for r in second_data["results"]}
        self.assertFalse(first_ids & second_ids)

    def test_page_size_parameter(self):
        self.authenticate(self.operator)
        response = self.client.get(f"{API}/lecturas/", {"page_size": 10, "page": 3})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["results"]), 5)
