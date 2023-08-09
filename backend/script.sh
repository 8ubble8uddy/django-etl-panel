#!/bin/bash
postgres_ready() {
    $(which curl) http://$POSTGRES_HOST:$POSTGRES_PORT/ 2>&1 | grep '52'
}

redis_ready() {
    exec 3<>/dev/tcp/$REDIS_HOST/$REDIS_PORT && echo -e "PING\r\n" >&3 && head -c 7 <&3 | grep 'PONG'
}

until redis_ready; do
  >&2 echo 'Waiting for Redis to become available...'
  sleep 1
done
>&2 echo 'Redis is available.'

until postgres_ready; do
  >&2 echo 'Waiting for PostgreSQL to become available...'
  sleep 1
done
>&2 echo 'PostgreSQL is available.'

python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser --noinput
gunicorn core.wsgi:application --bind 0:8000