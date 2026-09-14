#!/bin/sh
set -eu

python src/manage.py migrate --noinput
exec gunicorn projeto_aplicado.wsgi:application \
	--bind 0.0.0.0:8000 \
	--workers "${GUNICORN_WORKERS:-2}" \
	--timeout "${GUNICORN_TIMEOUT:-60}"
