#!/bin/bash
if [ ! -f "credentials/sylvan-harmony-404807-02d7953b3a5c.json" ] \
    && [ -n "${GOOGLE_APPLICATION_CREDENTIALS_JSON}" ]; then
    mkdir -p credentials
    echo $GOOGLE_APPLICATION_CREDENTIALS_JSON > credentials/sylvan-harmony-404807-02d7953b3a5c.json
fi

python manage.py migrate

python manage.py loaddata api/fixtures/*

python manage.py runserver 0.0.0.0:80