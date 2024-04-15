#!/bin/sh
# 0 8 1 * * docker-compose exec web /code/monthly_cronjob.sh >> /tmp/monthly_stat.log 2>&1

python ./manage.py shell < ./scripts/system/monthly_stat.py

