from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import Permission, User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import UserProfile
from monitoring.models import (
    Category,
    ConsumptionReading,
    Device,
    Manufacturer,
    Organization,
    Zone,
    ZoneStatus,
    ZoneType,
)

from .pagination import DEFAULT_PAGE_SIZE, SESSION_KEY

PASSWORD = "Prueba#Segura2026"


class SessionPaginationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        organization = Organization.objects.create(name="Org", tax_id="1-9")
        zone = Zone.objects.create(
            organization=organization,
            zone_type=ZoneType.objects.create(name="Oficina"),
            status=ZoneStatus.objects.create(name="Operativa"),
            name="Zona",
            consumption_limit_kwh=Decimal("100"),
        )
        device = Device.objects.create(
            zone=zone,
            category=Category.objects.create(name="Cat"),
            manufacturer=Manufacturer.objects.create(name="Fab"),
            name="Equipo",
            serial_number="SN-0001",
            installed_on="2025-01-01",
            nominal_consumption_kwh=Decimal("10"),
        )
        now = timezone.now()
        ConsumptionReading.objects.bulk_create(
            ConsumptionReading(
                device=device,
                reading_at=now - timedelta(hours=i + 1),
                consumption_kwh=Decimal("5"),
            )
            for i in range(40)
        )
        user = User.objects.create_user("lector", password=PASSWORD)
        UserProfile.objects.create(user=user, organization=organization)
        user.user_permissions.add(Permission.objects.get(codename="view_consumptionreading"))

    def setUp(self):
        self.client.login(username="lector", password=PASSWORD)
        self.url = reverse("monitoring:reading_list")

    def page_size(self, response):
        return len(response.context["readings"])

    def test_default_is_15(self):
        response = self.client.get(self.url)
        self.assertEqual(self.page_size(response), DEFAULT_PAGE_SIZE)

    def test_allowed_sizes(self):
        for size in (5, 15, 30):
            response = self.client.get(self.url, {"per_page": size})
            self.assertEqual(self.page_size(response), size)

    def test_size_persists_in_session(self):
        self.client.get(self.url, {"per_page": 5})
        self.assertEqual(self.client.session[SESSION_KEY], 5)
        response = self.client.get(self.url, {"page": 2})
        self.assertEqual(self.page_size(response), 5)
        self.assertEqual(response.context["page_obj"].number, 2)

    def test_invalid_values_are_normalized(self):
        for value in ("1000", "0", "-5", "abc", "7"):
            response = self.client.get(self.url, {"per_page": value})
            self.assertEqual(self.page_size(response), DEFAULT_PAGE_SIZE)
            self.assertEqual(self.client.session[SESSION_KEY], DEFAULT_PAGE_SIZE)

    def test_tampered_session_value_is_normalized(self):
        session = self.client.session
        session[SESSION_KEY] = 500
        session.save()
        response = self.client.get(self.url)
        self.assertEqual(self.page_size(response), DEFAULT_PAGE_SIZE)

    def test_out_of_range_page_shows_last_page(self):
        response = self.client.get(self.url, {"page": 999})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["page_obj"].number, 3)
