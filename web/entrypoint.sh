#!/bin/bash
set -e

echo "Waiting for postgres..."
while ! pg_isready -h postgres -p 5432 > /dev/null 2>&1; do
  sleep 1
done
echo "PostgreSQL started"

echo "Running migrations..."
python manage.py migrate --noinput

echo "Creating superuser if not exists..."
python manage.py shell << END
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superuser created')
else:
    print('Superuser already exists')
END

echo "Creating demo data..."
python manage.py create_demo_data || true

exec "$@"
