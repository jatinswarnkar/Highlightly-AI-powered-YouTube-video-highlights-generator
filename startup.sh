#!/bin/bash

# Run migrations
python manage.py migrate --noinput

# Collect static files
python manage.py collectstatic --noinput

# Start Gunicorn with extended timeout for ML model loading
gunicorn core.wsgi:application --bind 0.0.0.0:8000 --workers 2 --timeout 300
