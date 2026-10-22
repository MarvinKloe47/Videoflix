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
    init)
        # Create the custom User's initial migration before resolving admin/JWT deps.
        python manage.py makemigrations auth_app video_app --noinput
        python manage.py migrate --noinput
        # The email-based administrator can only be created after its table exists.
        python manage.py bootstrap_admin
        python manage.py collectstatic --noinput
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
