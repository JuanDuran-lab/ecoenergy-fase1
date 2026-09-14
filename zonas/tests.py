from decimal import Decimal

from django.contrib.auth.models import Permission, User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from .models import (
    Categoria,
    Dispositivo,
    EstadoZona,
    Organizacion,
    PerfilUsuario,
    TipoZona,
    Zona,
)


class EcoEnergyBaseTest(TestCase):
    def setUp(self):
        self.org_norte = Organizacion.objects.create(
            nombre="EcoEnergy Norte",
            rut="76.111.111-1",
            activa=True,
        )
        self.org_sur = Organizacion.objects.create(
            nombre="EcoEnergy Sur",
            rut="76.222.222-2",
            activa=True,
        )

        self.categoria = Categoria.objects.create(
            nombre="Climatización",
            descripcion="",
            activa=True,
        )

        self.tipo_zona = TipoZona.objects.create(
            nombre="Oficina",
            descripcion="",
            activo=True,
        )

        self.estado_zona = EstadoZona.objects.create(
            nombre="Operativa",
            descripcion="",
        )

        self.zona_norte = Zona.objects.create(
            organizacion=self.org_norte,
            tipo=self.tipo_zona,
            estado=self.estado_zona,
            nombre="Recepción Norte",
            descripcion="",
            limite_kwh=Decimal("100.00"),
        )

        self.zona_sur = Zona.objects.create(
            organizacion=self.org_sur,
            tipo=self.tipo_zona,
            estado=self.estado_zona,
            nombre="Recepción Sur",
            descripcion="",
            limite_kwh=Decimal("90.00"),
        )

        self.dispositivo_norte = Dispositivo.objects.create(
            zona=self.zona_norte,
            categoria=self.categoria,
            nombre="Aire acondicionado Norte",
            consumo_kwh=Decimal("45.00"),
            activo=True,
        )

        self.dispositivo_sur = Dispositivo.objects.create(
            zona=self.zona_sur,
            categoria=self.categoria,
            nombre="Aire acondicionado Sur",
            consumo_kwh=Decimal("30.00"),
            activo=True,
        )

        self.operador_norte = User.objects.create_user(
            username="operador_norte",
            password="EcoNorte2026!",
            is_staff=True,
        )

        PerfilUsuario.objects.create(
            usuario=self.operador_norte,
            organizacion=self.org_norte,
        )

        permisos = Permission.objects.filter(
            content_type__app_label="zonas",
            codename__in=[
                "view_zona",
                "add_zona",
                "change_zona",
                "view_dispositivo",
                "add_dispositivo",
                "change_dispositivo",
            ],
        )
        self.operador_norte.user_permissions.set(permisos)


class ModeloValidationTests(EcoEnergyBaseTest):
    def test_zona_no_permite_limite_cero(self):
        zona = Zona(
            organizacion=self.org_norte,
            tipo=self.tipo_zona,
            estado=self.estado_zona,
            nombre="Zona inválida",
            descripcion="",
            limite_kwh=Decimal("0.00"),
        )

        with self.assertRaises(ValidationError):
            zona.full_clean()

    def test_dispositivo_no_permite_consumo_negativo(self):
        dispositivo = Dispositivo(
            zona=self.zona_norte,
            categoria=self.categoria,
            nombre="Dispositivo inválido",
            consumo_kwh=Decimal("-1.00"),
            activo=True,
        )

        with self.assertRaises(ValidationError):
            dispositivo.full_clean()


class AdminScopingTests(EcoEnergyBaseTest):
    def setUp(self):
        super().setUp()
        self.client.login(
            username="operador_norte",
            password="EcoNorte2026!",
        )

    def test_operador_norte_ve_solo_sus_zonas(self):
        response = self.client.get(
            reverse("admin:zonas_zona_changelist")
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Recepción Norte")
        self.assertNotContains(response, "Recepción Sur")

    def test_operador_norte_ve_solo_sus_dispositivos(self):
        response = self.client.get(
            reverse("admin:zonas_dispositivo_changelist")
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Aire acondicionado Norte",
        )
        self.assertNotContains(
            response,
            "Aire acondicionado Sur",
        )

    def test_operador_norte_no_puede_abrir_zona_sur(self):
        response = self.client.get(
            reverse(
                "admin:zonas_zona_change",
                args=[self.zona_sur.pk],
            ),
            follow=True,
        )

        self.assertNotEqual(response.status_code, 500)

        self.assertContains(
            response,
            "doesn’t exist",
            status_code=200,
        )


class VistaPublicaTests(EcoEnergyBaseTest):
    def test_listado_zonas_responde_correctamente(self):
        response = self.client.get("/zonas/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Recepción Norte")
        self.assertContains(response, "Recepción Sur")

    def test_resumen_marca_limite_superado(self):
        Dispositivo.objects.create(
            zona=self.zona_norte,
            categoria=self.categoria,
            nombre="Equipo adicional",
            consumo_kwh=Decimal("70.00"),
            activo=True,
        )

        response = self.client.get("/resumen-zonas/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "LÍMITE SUPERADO",
        )