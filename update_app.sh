#!/bin/bash
git pull
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
kill -HUP `cat gunicorn.pid`
killall open511-importer