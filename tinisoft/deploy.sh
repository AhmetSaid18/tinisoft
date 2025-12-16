#!/bin/bash
# Deployment script for Tinisoft

set -e

echo "=== Tinisoft Deployment Script ==="

# Environment check
if [ ! -f .env ]; then
    echo "ERROR: .env file not found!"
    echo "Please create .env file from .env.example"
    exit 1
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Build and start services
echo "Building Docker images..."
docker-compose build

echo "Starting services..."
docker-compose up -d

# Wait for postgres to be ready
echo "Waiting for PostgreSQL..."
sleep 10

# Run migrations
echo "Running migrations..."
docker-compose exec -T backend python manage.py migrate

# Create superuser (optional)
echo "Do you want to create a superuser? (y/n)"
read -r response
if [ "$response" = "y" ]; then
    docker-compose exec backend python manage.py createsuperuser
fi

# Collect static files
echo "Collecting static files..."
docker-compose exec -T backend python manage.py collectstatic --noinput

echo "=== Deployment completed ==="
echo "Backend: http://localhost:8000"
echo "Check logs: docker-compose logs -f backend"

