@echo off
REM Deployment script for Tinisoft (Windows)

echo === Tinisoft Deployment Script ===

REM Environment check
if not exist .env (
    echo ERROR: .env file not found!
    echo Please create .env file from .env.example
    pause
    exit /b 1
)

REM Build and start services
echo Building Docker images...
docker-compose build

echo Starting services...
docker-compose up -d

REM Wait for postgres to be ready
echo Waiting for PostgreSQL...
timeout /t 10 /nobreak >nul

REM Run migrations
echo Running migrations...
docker-compose exec -T backend python manage.py migrate

REM Collect static files
echo Collecting static files...
docker-compose exec -T backend python manage.py collectstatic --noinput

echo === Deployment completed ===
echo Backend: http://localhost:8000
echo Check logs: docker-compose logs -f backend
pause

