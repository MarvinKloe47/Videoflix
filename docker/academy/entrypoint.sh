#!/bin/sh
# Own extension. The upstream backend.entrypoint.sh remains byte-for-byte intact.
set -eu

attempt=0
until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -q; do
    attempt=$((attempt + 1))
    if [ "$attempt" -ge 60 ]; then
        echo "PostgreSQL readiness timed out" >&2
        exit 1
    fi
    sleep 1
done

case "${1:-web}" in
    migrate)
        python manage.py migrate --noinput
        python manage.py collectstatic --noinput
        python /app/academy/bootstrap_admin.py
        ;;
    worker)
        exec python manage.py rqworker default
        ;;
    web)
        exec gunicorn core.wsgi:application --bind 0.0.0.0:8000 --workers 2
        ;;
    *)
        exec "$@"
        ;;
esac
