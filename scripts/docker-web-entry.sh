#!/bin/bash
set -o errexit       # ← 任何指令失敗就中止，避免 migrate 失敗還繼續啟動 gunicorn
set -o pipefail
set -o nounset

cd /code

python manage.py migrate --no-input
python manage.py collectstatic --no-input --clear 

exec gunicorn \
    --bind 0.0.0.0:8001 \
    --workers=2 \
    --timeout 60 \
    --error-logfile - \
    conf.wsgi:application