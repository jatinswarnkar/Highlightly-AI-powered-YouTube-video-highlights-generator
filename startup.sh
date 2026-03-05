#!/bin/bash

# Run migrations
python manage.py migrate --noinput

# Collect static files
python manage.py collectstatic --noinput

# Start Gunicorn
gunicorn core.wsgi:application --bind 0.0.0.0:8000 --workers 3
