#!/usr/bin/env bash
# Actualiza la aplicación en la instancia EC2 con el último commit de main.
# Uso (dentro de la instancia):  bash deploy/update.sh
set -euo pipefail

cd /home/ubuntu/ecoenergy
git pull origin main
.venv/bin/pip install -r requirements.txt
.venv/bin/python manage.py migrate --noinput
.venv/bin/python manage.py collectstatic --noinput
.venv/bin/python manage.py check
# Revisión de seguridad informativa (avisa si falta HTTPS o SMTP).
.venv/bin/python manage.py check --deploy || true
sudo systemctl restart ecoenergy
echo "Despliegue actualizado: $(git rev-parse --short HEAD)"
