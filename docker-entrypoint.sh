#!/bin/bash
set -e

wait_for() {
    echo "Waiting for $3..."
    while ! nc -z "$1" "$2" 2>/dev/null; do sleep 1; done
    echo "$3 is ready!"
}

[ -n "$DB_HOST" ] && wait_for "$DB_HOST" "${DB_PORT:-5432}" "PostgreSQL"

if [ -n "$CELERY_BROKER_URL" ]; then
    REDIS_HOST=$(echo "$CELERY_BROKER_URL" | sed -E 's|redis://(:.*@)?([^:]+):([0-9]+)/.*|\2|')
    REDIS_PORT=$(echo "$CELERY_BROKER_URL" | sed -E 's|redis://(:.*@)?([^:]+):([0-9]+)/.*|\3|')
    [ -n "$REDIS_HOST" ] && wait_for "$REDIS_HOST" "$REDIS_PORT" "Redis"
fi

case "$1" in
    web)
        python manage.py migrate --noinput
        python manage.py collectstatic --noinput --clear 2>/dev/null || true
        exec gunicorn harry.wsgi:application \
            --bind 0.0.0.0:8000 \
            --workers ${GUNICORN_WORKERS:-4} \
            --timeout ${GUNICORN_TIMEOUT:-120} \
            --access-logfile - \
            --error-logfile -
        ;;
    celery-worker)
        exec celery -A harry worker \
            --loglevel=${CELERY_LOG_LEVEL:-info} \
            --concurrency=${CELERY_CONCURRENCY:-4}
        ;;
    celery-beat)
        exec celery -A harry beat \
            --loglevel=${CELERY_LOG_LEVEL:-info} \
            --schedule=/app/celerybeat-schedule/celerybeat-schedule.db
        ;;
    *)
        exec "$@"
        ;;
esac