#!/bin/bash
python manage.py migrate

python manage.py loaddata api/fixtures/*

python manage.py runserver 0.0.0.0:8000