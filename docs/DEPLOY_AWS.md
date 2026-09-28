# Despliegue en AWS Academy (EC2 + Gunicorn + Nginx)

Guía paso a paso para dejar EcoEnergy publicado en una instancia EC2 del
**AWS Academy Learner Lab**. Arquitectura:

```
Navegador ──HTTP:80──> Nginx ──socket──> Gunicorn ──> Django ──> SQLite (o PostgreSQL)
                        │
                        ├── /static/  -> staticfiles/  (collectstatic)
                        └── /media/   -> media/        (imágenes subidas)
```

> **Importante sobre el Learner Lab:** el laboratorio se apaga al terminar la
> sesión (≈4 horas) y la **IP pública cambia** cada vez que la instancia se
> detiene y vuelve a iniciar. Para la revisión: inicia el laboratorio con
> tiempo, verifica la URL y, si cambió la IP, actualiza
> `DJANGO_ALLOWED_HOSTS` y `DJANGO_CSRF_TRUSTED_ORIGINS` (paso 7).
> Una **Elastic IP** evita este problema si tu laboratorio lo permite.

---

## 1. Crear la instancia EC2

En la consola de AWS (botón **AWS** del Learner Lab) → **EC2 → Launch instance**:

| Opción | Valor |
|---|---|
| Nombre | `ecoenergy` |
| AMI | **Ubuntu Server 24.04 LTS** (trae Python 3.12, requerido por Django 6.1) |
| Tipo | `t2.micro` o `t3.micro` |
| Key pair | `vockey` (la del laboratorio) o una nueva |
| Security group | Reglas de entrada: **SSH (22)** desde tu IP y **HTTP (80)** desde `0.0.0.0/0` |
| Almacenamiento | 8–16 GB |

Opcional: **EC2 → Elastic IPs → Allocate** y asociarla a la instancia.

## 2. Conectarse por SSH

Descarga la llave desde *AWS Details → Download PEM* (`labsuser.pem`) y:

```bash
chmod 400 labsuser.pem
ssh -i labsuser.pem ubuntu@<IP_PUBLICA>
```

También puedes usar **EC2 → Connect → EC2 Instance Connect** desde el navegador.

## 3. Instalar dependencias del sistema

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip git nginx
```

## 4. Clonar el proyecto y crear el entorno virtual

```bash
cd /home/ubuntu
git clone https://github.com/JuanDuran-lab/ecoenergy-fase1.git ecoenergy
cd ecoenergy
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt
```

## 5. Crear el archivo `.env` de producción

```bash
cp .env.example .env
nano .env
```

Valores mínimos (reemplaza `<IP_PUBLICA>`):

```ini
DJANGO_SECRET_KEY=<pega aquí una clave generada, ver abajo>
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=<IP_PUBLICA>
DJANGO_CSRF_TRUSTED_ORIGINS=http://<IP_PUBLICA>
DJANGO_USE_HTTPS=False

DB_ENGINE=sqlite
DB_NAME=db.sqlite3

SEED_ADMIN_PASSWORD=<contraseña segura>
SEED_SUPERVISOR_PASSWORD=<contraseña segura>
SEED_READER_PASSWORD=<contraseña segura>
SEED_ADMIN_EMAIL=<correo real para probar la recuperación>
SEED_SUPERVISOR_EMAIL=<correo real>
SEED_READER_EMAIL=<correo real>

# SMTP para que el código de 6 dígitos llegue por correo (ver paso 10)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=<tu_correo@gmail.com>
EMAIL_HOST_PASSWORD=<contraseña de aplicación de 16 caracteres>
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=EcoEnergy <tu_correo@gmail.com>
```

Generar la `DJANGO_SECRET_KEY`:

```bash
.venv/bin/python -c "import secrets; print(secrets.token_urlsafe(50))"
```

Protege el archivo: `chmod 600 .env`

## 6. Base de datos, datos de prueba y estáticos

```bash
.venv/bin/python manage.py migrate
.venv/bin/python manage.py seed_data          # 1.521 registros + 3 usuarios
.venv/bin/python manage.py collectstatic --noinput
mkdir -p media
.venv/bin/python manage.py check
```

## 7. Gunicorn como servicio (systemd)

```bash
sudo cp deploy/gunicorn.service /etc/systemd/system/ecoenergy.service
sudo systemctl daemon-reload
sudo systemctl enable --now ecoenergy
sudo systemctl status ecoenergy        # debe decir "active (running)"
```

Si cambias el `.env` (por ejemplo, porque cambió la IP):

```bash
sudo systemctl restart ecoenergy
```

## 8. Nginx

```bash
sudo cp deploy/nginx-ecoenergy.conf /etc/nginx/sites-available/ecoenergy
sudo ln -sf /etc/nginx/sites-available/ecoenergy /etc/nginx/sites-enabled/ecoenergy
sudo rm -f /etc/nginx/sites-enabled/default
# Nginx (usuario www-data) necesita poder leer staticfiles/ y media/
sudo chmod 755 /home/ubuntu
sudo nginx -t
sudo systemctl restart nginx
```

Abrir en el navegador: `http://<IP_PUBLICA>/`

## 9. Actualizar después de un nuevo merge a `main`

```bash
cd /home/ubuntu/ecoenergy
bash deploy/update.sh
```

El script hace `git pull`, instala dependencias, migra, ejecuta
`collectstatic` y reinicia Gunicorn. Muestra el hash del commit desplegado.

## 10. Correo para la recuperación de contraseña

Con Gmail:

1. Activa la verificación en dos pasos en la cuenta de Google.
2. Crea una **contraseña de aplicación** en <https://myaccount.google.com/apppasswords>.
3. Úsala en `EMAIL_HOST_PASSWORD` y reinicia el servicio.

Si no configuras SMTP (`EMAIL_HOST` vacío), el correo con el código se
escribe en el log del servicio. Se puede leer durante la demo con:

```bash
sudo journalctl -u ecoenergy -n 50 --no-pager | grep -A2 "código"
```

## 11. Solución de problemas

| Síntoma | Causa probable | Solución |
|---|---|---|
| `Bad Request (400)` | La IP no está en `DJANGO_ALLOWED_HOSTS` | Corregir `.env` y `sudo systemctl restart ecoenergy` |
| `403 CSRF verification failed` al iniciar sesión | Falta la URL en `DJANGO_CSRF_TRUSTED_ORIGINS` | Agregar `http://<IP_PUBLICA>` y reiniciar |
| `502 Bad Gateway` | Gunicorn detenido | `sudo journalctl -u ecoenergy -n 50` |
| Página sin estilos propios o imágenes rotas | Permisos de lectura para Nginx | `sudo chmod 755 /home/ubuntu` y revisar `collectstatic` |
| `413 Request Entity Too Large` | Archivo mayor al límite de Nginx | Normal si pesa > 5 MB; Django rechaza > 2 MB |
| La página no carga | Security group sin puerto 80, o laboratorio detenido | Revisar reglas de entrada y el estado del lab |

## Advertencias esperadas de `check --deploy`

Al no tener dominio ni certificado, el sitio funciona por **HTTP**. Por eso
`manage.py check --deploy` advierte sobre HSTS, `SECURE_SSL_REDIRECT` y
cookies seguras. Si se configura HTTPS (por ejemplo, con un dominio y
Certbot), basta con `DJANGO_USE_HTTPS=True` para activar las cookies seguras.
