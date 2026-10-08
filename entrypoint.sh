#!/bin/sh
# Запуск контейнера: миграции, затем gunicorn
set -e

python manage.py migrate --no-input

exec gunicorn core.wsgi:application \
    --bind "0.0.0.0:${PORT:-8000}" \
    --workers 1 --threads 4 --timeout 180
