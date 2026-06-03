#!/bin/bash

# Prevent interactive prompts (like timezone selection) from hanging the installation
export DEBIAN_FRONTEND=noninteractive

# Install ffmpeg (not included in Azure App Service Python runtime)
apt-get update && apt-get install -y --no-install-recommends ffmpeg

# Run migrations
python manage.py migrate --noinput

# Collect static files
python manage.py collectstatic --noinput

# Start Gunicorn with extended timeout for ML model loading
gunicorn core.wsgi:application --bind 0.0.0.0:8000 --workers 2 --timeout 300
