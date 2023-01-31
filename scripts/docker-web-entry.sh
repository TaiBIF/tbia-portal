#!/bin/bash

cd /code

# npm run build

python manage.py migrate --no-input
python manage.py collectstatic --no-input

gunicorn --bind 0.0.0.0:8001 --workers=2 --timeout 60 conf.wsgi:application
