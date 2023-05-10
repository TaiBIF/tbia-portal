#!/bin/sh

python ./manage.py shell < ./scripts/system/check_file_expired.py
python ./manage.py shell < ./scripts/system/sensitive_request_review

