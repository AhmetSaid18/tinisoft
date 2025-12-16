#!/bin/bash
# Container içinde migration script

echo "=== Tinisoft Migration Script (Container) ==="

# Container'ın çalıştığını kontrol et
if ! docker ps | grep -q tinisoft-backend; then
    echo "ERROR: tinisoft-backend container is not running!"
    echo "Start it with: docker-compose up -d"
    exit 1
fi

echo "1. Creating migrations..."
docker exec -it tinisoft-backend python manage.py makemigrations

echo "2. Applying migrations..."
docker exec -it tinisoft-backend python manage.py migrate

echo "3. Collecting static files..."
docker exec -it tinisoft-backend python manage.py collectstatic --noinput

echo ""
echo "=== Migration completed ==="
echo ""
echo "Do you want to create a superuser? (y/n)"
read -r response
if [ "$response" = "y" ]; then
    docker exec -it tinisoft-backend python manage.py createsuperuser
fi

