#!/bin/sh
set -eu

cd "$(dirname "$0")"

if [ "${DJANGO_ENV:-}" != "production" ]; then
    printf '%s\n' 'Refusing to start unless DJANGO_ENV=production.' >&2
    exit 1
fi

python manage.py migrate --noinput

exec gunicorn --bind "0.0.0.0:${PORT:?Render must provide PORT}" config.wsgi:application
