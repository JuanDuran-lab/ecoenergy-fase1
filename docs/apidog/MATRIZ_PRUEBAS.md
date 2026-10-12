# Matriz de pruebas de la API (Apidog)

Ejecución completa de la colección `EcoEnergy_API.postman_collection.json` contra el servidor local (`http://127.0.0.1:8000`), con la base recién cargada por `python manage.py seed_data` (2.186 registros). Fecha: 12-10-2026. Commit: `aa7d3cb`.

**Resultado:** 56 solicitudes, 138 verificaciones, 0 fallidas.

Los tokens JWT y las contraseñas no aparecen: los tokens se reemplazan por `<oculto>` y las contraseñas se leen del entorno de Apidog. Los ids de la URL son los de esta ejecución; la colección los captura en cada corrida, así funciona con cualquier base cargada.

Identidades: **Administrador API** = `supervisor_norte` (EcoEnergy Norte), **Operador API** = `lector_sur` (EcoEnergy Sur), **Sin rol API** = `invitado_centro` (EcoEnergy Centro).


## 01 JWT

| N.º | Solicitud | Método | URL | Identidad | Esperado | Observado | Respuesta representativa |
|---|---|---|---|---|---|---|---|
| 1 | Obtener token · Administrador API | POST | `/api/token/` | Administrador API (supervisor_norte) | 200 | 200 ✅ | `{"refresh":"<oculto>","access":"<oculto>"}` |
| 2 | Renovar access · refresh | POST | `/api/token/refresh/` | Administrador API (refresh token) | 200 | 200 ✅ | `{"access":"<oculto>"}` |
| 3 | Obtener token · Operador API | POST | `/api/token/` | Operador API (lector_sur) | 200 | 200 ✅ | `{"refresh":"<oculto>","access":"<oculto>"}` |
| 4 | Obtener token · usuario sin rol API | POST | `/api/token/` | Sin rol API (invitado_centro) | 200 | 200 ✅ | `{"refresh":"<oculto>","access":"<oculto>"}` |
| 5 | Credenciales incorrectas → 401 | POST | `/api/token/` | supervisor_norte con contraseña incorrecta | 401 | 401 ✅ | `{"detail":"No se encontró una cuenta de usuario activa para las credenciales provistas"}` |

## 02 Autenticación y roles

| N.º | Solicitud | Método | URL | Identidad | Esperado | Observado | Respuesta representativa |
|---|---|---|---|---|---|---|---|
| 6 | Sin token → 401 | GET | `/api/zonas/` | Sin token | 401 | 401 ✅ | `{"detail":"Las credenciales de autenticación no se proveyeron."}` |
| 7 | Token inválido → 401 | GET | `/api/zonas/` | Token inválido | 401 | 401 ✅ | `{"detail":"El token provisto no es válido para ningún tipo de token","code":"token_not_valid","messages":[{"t…` |
| 8 | Operador · GET zonas → 200 | GET | `/api/zonas/` | Operador API (lector_sur) | 200 | 200 ✅ | `{"count":8,"total_pages":1,"page":1,"page_size":20,"next":null,"previous":null,"results":[{"id":12,"organizat…` |
| 9 | Operador · POST zona → 403 | POST | `/api/zonas/` | Operador API (lector_sur) | 403 | 403 ✅ | `{"detail":"El rol Operador API solo permite consultar (GET)."}` |
| 10 | Sin rol API · GET zonas → 403 | GET | `/api/zonas/` | Sin rol API (invitado_centro) | 403 | 403 ✅ | `{"detail":"Tu usuario no tiene un rol API asignado."}` |
| 11 | Sin rol API · GET lecturas → 403 | GET | `/api/lecturas/` | Sin rol API (invitado_centro) | 403 | 403 ✅ | `{"detail":"Tu usuario no tiene un rol API asignado."}` |

## 03 Cobertura de modelos

| N.º | Solicitud | Método | URL | Identidad | Esperado | Observado | Respuesta representativa |
|---|---|---|---|---|---|---|---|
| 12 | GET lista · zonas | GET | `/api/zonas/` | Administrador API (supervisor_norte) | 200 | 200 ✅ | `{"count":8,"total_pages":1,"page":1,"page_size":20,"next":null,"previous":null,"results":[{"id":4,"organizati…` |
| 13 | GET detalle · zonas | GET | `/api/zonas/4/` | Administrador API (supervisor_norte) | 200 | 200 ✅ | `{"id":4,"organization":1,"organization_name":"EcoEnergy Norte","name":"Bodega principal","zone_type":2,"zone_…` |
| 14 | GET lista · dispositivos | GET | `/api/dispositivos/` | Administrador API (supervisor_norte) | 200 | 200 ✅ | `{"count":40,"total_pages":2,"page":1,"page_size":20,"next":"http://127.0.0.1:8000/api/dispositivos/?page=2","…` |
| 15 | GET detalle · dispositivos | GET | `/api/dispositivos/17/` | Administrador API (supervisor_norte) | 200 | 200 ✅ | `{"id":17,"zone":4,"zone_name":"Bodega principal","organization":1,"organization_name":"EcoEnergy Norte","name…` |
| 16 | GET lista · fabricantes | GET | `/api/fabricantes/` | Administrador API (supervisor_norte) | 200 | 200 ✅ | `{"count":8,"total_pages":1,"page":1,"page_size":20,"next":null,"previous":null,"results":[{"id":3,"name":"ABB…` |
| 17 | GET detalle · fabricantes | GET | `/api/fabricantes/3/` | Administrador API (supervisor_norte) | 200 | 200 ✅ | `{"id":3,"name":"ABB","country":"Suiza","website":"https://new.abb.com","is_active":true,"created_at":"2026-10…` |
| 18 | GET lista · categorias | GET | `/api/categorias/` | Administrador API (supervisor_norte) | 200 | 200 ✅ | `{"count":6,"total_pages":1,"page":1,"page_size":20,"next":null,"previous":null,"results":[{"id":1,"name":"Cli…` |
| 19 | GET detalle · categorias | GET | `/api/categorias/1/` | Administrador API (supervisor_norte) | 200 | 200 ✅ | `{"id":1,"name":"Climatización","description":"Aire acondicionado, calefacción y ventilación.","is_active":tru…` |
| 20 | GET lista · lecturas | GET | `/api/lecturas/` | Administrador API (supervisor_norte) | 200 | 200 ✅ | `{"count":600,"total_pages":30,"page":1,"page_size":20,"next":"http://127.0.0.1:8000/api/lecturas/?page=2","pr…` |
| 21 | GET detalle · lecturas | GET | `/api/lecturas/60/` | Administrador API (supervisor_norte) | 200 | 200 ✅ | `{"id":60,"device":4,"device_name":"Sensor de humedad 04","zone":1,"zone_name":"Recepción","organization_name"…` |
| 22 | GET lista · alertas | GET | `/api/alertas/` | Administrador API (supervisor_norte) | 200 | 200 ✅ | `{"count":77,"total_pages":4,"page":1,"page_size":20,"next":"http://127.0.0.1:8000/api/alertas/?page=2","previ…` |
| 23 | GET detalle · alertas | GET | `/api/alertas/14/` | Administrador API (supervisor_norte) | 200 | 200 ✅ | `{"id":14,"zone":2,"zone_name":"Oficina administrativa","organization_name":"EcoEnergy Norte","device":7,"devi…` |

## 04 CRUD principales

| N.º | Solicitud | Método | URL | Identidad | Esperado | Observado | Respuesta representativa |
|---|---|---|---|---|---|---|---|
| 24 | Categoría · POST categoría → 201 | POST | `/api/categorias/` | Administrador API (supervisor_norte) | 201 | 201 ✅ | `{"id":7,"name":"Categoría API 996584","description":"Creada desde Apidog","is_active":true,"created_at":"2026…` |
| 25 | Categoría · GET categoría → 200 | GET | `/api/categorias/7/` | Administrador API (supervisor_norte) | 200 | 200 ✅ | `{"id":7,"name":"Categoría API 996584","description":"Creada desde Apidog","is_active":true,"created_at":"2026…` |
| 26 | Categoría · PATCH categoría → 200 | PATCH | `/api/categorias/7/` | Administrador API (supervisor_norte) | 200 | 200 ✅ | `{"id":7,"name":"Categoría API 996584","description":"Descripción actualizada","is_active":true,"created_at":"…` |
| 27 | Categoría · PUT categoría → 200 | PUT | `/api/categorias/7/` | Administrador API (supervisor_norte) | 200 | 200 ✅ | `{"id":7,"name":"Categoría API 996584 editada","description":"Reemplazo completo","is_active":true,"created_at…` |
| 28 | Fabricante · POST fabricante → 201 | POST | `/api/fabricantes/` | Administrador API (supervisor_norte) | 201 | 201 ✅ | `{"id":9,"name":"Fabricante API 996584","country":"Chile","website":"https://ejemplo.cl","is_active":true,"cre…` |
| 29 | Fabricante · GET fabricante → 200 | GET | `/api/fabricantes/9/` | Administrador API (supervisor_norte) | 200 | 200 ✅ | `{"id":9,"name":"Fabricante API 996584","country":"Chile","website":"https://ejemplo.cl","is_active":true,"cre…` |
| 30 | Fabricante · PATCH fabricante → 200 | PATCH | `/api/fabricantes/9/` | Administrador API (supervisor_norte) | 200 | 200 ✅ | `{"id":9,"name":"Fabricante API 996584","country":"Perú","website":"https://ejemplo.cl","is_active":true,"crea…` |
| 31 | Fabricante · PUT fabricante → 200 | PUT | `/api/fabricantes/9/` | Administrador API (supervisor_norte) | 200 | 200 ✅ | `{"id":9,"name":"Fabricante API 996584 editado","country":"Chile","website":"https://ejemplo.cl","is_active":t…` |
| 32 | Zona · POST zona → 201 | POST | `/api/zonas/` | Administrador API (supervisor_norte) | 201 | 201 ✅ | `{"id":25,"organization":1,"organization_name":"EcoEnergy Norte","name":"Zona API 996584","zone_type":2,"zone_…` |
| 33 | Zona · GET zona → 200 | GET | `/api/zonas/25/` | Administrador API (supervisor_norte) | 200 | 200 ✅ | `{"id":25,"organization":1,"organization_name":"EcoEnergy Norte","name":"Zona API 996584","zone_type":2,"zone_…` |
| 34 | Zona · PATCH zona → 200 | PATCH | `/api/zonas/25/` | Administrador API (supervisor_norte) | 200 | 200 ✅ | `{"id":25,"organization":1,"organization_name":"EcoEnergy Norte","name":"Zona API 996584","zone_type":2,"zone_…` |
| 35 | Zona · PUT zona → 200 | PUT | `/api/zonas/25/` | Administrador API (supervisor_norte) | 200 | 200 ✅ | `{"id":25,"organization":1,"organization_name":"EcoEnergy Norte","name":"Zona API 996584 editada","zone_type":…` |
| 36 | Dispositivo · POST dispositivo → 201 | POST | `/api/dispositivos/` | Administrador API (supervisor_norte) | 201 | 201 ✅ | `{"id":121,"zone":25,"zone_name":"Zona API 996584 editada","organization":1,"organization_name":"EcoEnergy Nor…` |
| 37 | Dispositivo · GET dispositivo → 200 | GET | `/api/dispositivos/121/` | Administrador API (supervisor_norte) | 200 | 200 ✅ | `{"id":121,"zone":25,"zone_name":"Zona API 996584 editada","organization":1,"organization_name":"EcoEnergy Nor…` |
| 38 | Dispositivo · PATCH dispositivo → 200 | PATCH | `/api/dispositivos/121/` | Administrador API (supervisor_norte) | 200 | 200 ✅ | `{"id":121,"zone":25,"zone_name":"Zona API 996584 editada","organization":1,"organization_name":"EcoEnergy Nor…` |
| 39 | Dispositivo · PUT dispositivo → 200 | PUT | `/api/dispositivos/121/` | Administrador API (supervisor_norte) | 200 | 200 ✅ | `{"id":121,"zone":25,"zone_name":"Zona API 996584 editada","organization":1,"organization_name":"EcoEnergy Nor…` |
| 40 | Dispositivo · DELETE dispositivo → 204 | DELETE | `/api/dispositivos/121/` | Administrador API (supervisor_norte) | 204 | 204 ✅ | `(sin cuerpo)` |
| 41 | Dispositivo · GET dispositivo eliminado → 404 | GET | `/api/dispositivos/121/` | Administrador API (supervisor_norte) | 404 | 404 ✅ | `{"detail":"El registro no existe o no pertenece a tu organización."}` |
| 42 | Eliminar zona y catálogos · DELETE zona → 204 | DELETE | `/api/zonas/25/` | Administrador API (supervisor_norte) | 204 | 204 ✅ | `(sin cuerpo)` |
| 43 | Eliminar zona y catálogos · GET zona eliminada → 404 | GET | `/api/zonas/25/` | Administrador API (supervisor_norte) | 404 | 404 ✅ | `{"detail":"El registro no existe o no pertenece a tu organización."}` |
| 44 | Eliminar zona y catálogos · DELETE fabricante → 204 | DELETE | `/api/fabricantes/9/` | Administrador API (supervisor_norte) | 204 | 204 ✅ | `(sin cuerpo)` |
| 45 | Eliminar zona y catálogos · DELETE categoría → 204 | DELETE | `/api/categorias/7/` | Administrador API (supervisor_norte) | 204 | 204 ✅ | `(sin cuerpo)` |

## 05 Validaciones y errores

| N.º | Solicitud | Método | URL | Identidad | Esperado | Observado | Respuesta representativa |
|---|---|---|---|---|---|---|---|
| 46 | Validación de campo: número de serie → 400 | POST | `/api/dispositivos/` | Administrador API (supervisor_norte) | 400 | 400 ✅ | `{"serial_number":["Solo mayúsculas, números y guiones (4 a 40 caracteres)."]}` |
| 47 | Validación de campo: instalación futura → 400 | POST | `/api/dispositivos/` | Administrador API (supervisor_norte) | 400 | 400 ✅ | `{"installed_on":["La fecha de instalación no puede ser futura."]}` |
| 48 | Validación de relación: zona de otra organización → 400 | POST | `/api/dispositivos/` | Administrador API (supervisor_norte) | 400 | 400 ✅ | `{"zone":["El registro 12 no existe o no pertenece a tu organización."]}` |
| 49 | Regla de negocio: número de serie duplicado → 400 | POST | `/api/dispositivos/` | Administrador API (supervisor_norte) | 400 | 400 ✅ | `{"serial_number":["Ya existe un dispositivo con este número de serie."]}` |
| 50 | Id inexistente → 404 | GET | `/api/zonas/999999/` | Administrador API (supervisor_norte) | 404 | 404 ✅ | `{"detail":"El registro no existe o no pertenece a tu organización."}` |
| 51 | Fabricante con dispositivos → 409 | DELETE | `/api/fabricantes/8/` | Administrador API (supervisor_norte) | 409 | 409 ✅ | `{"detail":"No se puede eliminar el fabricante: está asociado a dispositivos. Puede marcarlo como inactivo (is…` |

## 06 Paginación

| N.º | Solicitud | Método | URL | Identidad | Esperado | Observado | Respuesta representativa |
|---|---|---|---|---|---|---|---|
| 52 | Lecturas página 1 → 200 | GET | `/api/lecturas/?page=1` | Operador API (lector_sur) | 200 | 200 ✅ | `{"count":600,"total_pages":30,"page":1,"page_size":20,"next":"http://127.0.0.1:8000/api/lecturas/?page=2","pr…` |
| 53 | Lecturas página 2 → 200 | GET | `/api/lecturas/?page=2` | Operador API (lector_sur) | 200 | 200 ✅ | `{"count":600,"total_pages":30,"page":2,"page_size":20,"next":"http://127.0.0.1:8000/api/lecturas/?page=3","pr…` |
| 54 | Tamaño de página 50 → 200 | GET | `/api/lecturas/?page_size=50&page=3` | Operador API (lector_sur) | 200 | 200 ✅ | `{"count":600,"total_pages":12,"page":3,"page_size":50,"next":"http://127.0.0.1:8000/api/lecturas/?page=4&page…` |

## 07 Scoping por organización

| N.º | Solicitud | Método | URL | Identidad | Esperado | Observado | Respuesta representativa |
|---|---|---|---|---|---|---|---|
| 55 | Administrador Norte · GET zona de Sur → 404 | GET | `/api/zonas/12/` | Administrador API (supervisor_norte) | 404 | 404 ✅ | `{"detail":"El registro no existe o no pertenece a tu organización."}` |
| 56 | Administrador Norte · PATCH zona de Sur → 404 | PATCH | `/api/zonas/12/` | Administrador API (supervisor_norte) | 404 | 404 ✅ | `{"detail":"El registro no existe o no pertenece a tu organización."}` |

## Respuestas completas de los casos principales

### JWT: obtener token (200)

`POST /api/token/` · Administrador API (supervisor_norte) · estado 200

```json
{
  "refresh": "<oculto>",
  "access": "<oculto>"
}
```

### Sin autenticación (401)

`GET /api/zonas/` · Sin token · estado 401

```json
{
  "detail": "Las credenciales de autenticación no se proveyeron."
}
```

### Operador intenta escribir (403)

`POST /api/zonas/` · Operador API (lector_sur) · estado 403

```json
{
  "detail": "El rol Operador API solo permite consultar (GET)."
}
```

### Usuario sin rol API (403)

`GET /api/zonas/` · Sin rol API (invitado_centro) · estado 403

```json
{
  "detail": "Tu usuario no tiene un rol API asignado."
}
```

### Crear dispositivo (201)

`POST /api/dispositivos/` · Administrador API (supervisor_norte) · estado 201

```json
{
  "id": 121,
  "zone": 25,
  "zone_name": "Zona API 996584 editada",
  "organization": 1,
  "organization_name": "EcoEnergy Norte",
  "name": "Medidor API 996584",
  "serial_number": "EE-API-996584",
  "category": 7,
  "category_name": "Categoría API 996584 editada",
  "manufacturer": 9,
  "manufacturer_name": "Fabricante API 996584 editado",
  "nominal_consumption_kwh": "12.50",
  "installed_on": "2026-01-15",
  "is_active": true,
  "image": null,
  "created_at": "2026-10-12T11:23:17.481715-03:00",
  "updated_at": "2026-10-12T11:23:17.481738-03:00"
}
```

### Validación de campo (400)

`POST /api/dispositivos/` · Administrador API (supervisor_norte) · estado 400

```json
{
  "serial_number": [
    "Solo mayúsculas, números y guiones (4 a 40 caracteres)."
  ]
}
```

### Validación de relación (400)

`POST /api/dispositivos/` · Administrador API (supervisor_norte) · estado 400

```json
{
  "zone": [
    "El registro 12 no existe o no pertenece a tu organización."
  ]
}
```

### Id inexistente (404)

`GET /api/zonas/999999/` · Administrador API (supervisor_norte) · estado 404

```json
{
  "detail": "El registro no existe o no pertenece a tu organización."
}
```

### Catálogo en uso (409)

`DELETE /api/fabricantes/8/` · Administrador API (supervisor_norte) · estado 409

```json
{
  "detail": "No se puede eliminar el fabricante: está asociado a dispositivos. Puede marcarlo como inactivo (is_active=false)."
}
```

### Lista paginada (página 2 de lecturas)

`GET /api/lecturas/?page=2` · Operador API (lector_sur) · estado 200

```json
{
  "count": 600,
  "total_pages": 30,
  "page": 2,
  "page_size": 20,
  "next": "http://127.0.0.1:8000/api/lecturas/?page=3",
  "previous": "http://127.0.0.1:8000/api/lecturas/",
  "results": [
    {
      "id": 780,
      "device": 52,
      "device_name": "Panel LED 02",
      "zone": 11,
      "zone_name": "Sala de servidores",
      "organization_name": "EcoEnergy Sur",
      "reading_at": "2026-10-10T05:30:00-03:00",
      "consumption_kwh": "18.28",
      "nominal_consumption_kwh": "21.54",
      "is_over_nominal": false,
      "notes": "",
      "created_at": "2026-10-12T11:23:02.622300-03:00"
    },
    "… (19 registros más)"
  ]
}
```
