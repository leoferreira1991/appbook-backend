#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate

# Seed commands are non-fatal — the app should start even if seeding fails
python manage.py seed_fake_users || echo "⚠️ seed_fake_users failed (non-fatal)"
python manage.py seed_activity || echo "⚠️ seed_activity failed (non-fatal)"
