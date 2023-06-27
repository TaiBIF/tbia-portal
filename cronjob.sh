#!/bin/sh
# 0 16 * * * docker exec tbia-web-stag-container /code/cronjob.sh >> /tmp/stat.log 2>&1

python ./manage.py shell < ./scripts/system/check_file_expired.py
python ./manage.py shell < ./scripts/system/sensitive_request_review.py

