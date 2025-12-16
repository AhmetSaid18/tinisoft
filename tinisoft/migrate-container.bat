@echo off
REM Container içinde migration script (Windows)

echo === Tinisoft Migration Script (Container) ===

REM Container'ın çalıştığını kontrol et
docker ps | findstr tinisoft-backend >nul
if errorlevel 1 (
    echo ERROR: tinisoft-backend container is not running!
    echo Start it with: docker-compose up -d
    pause
    exit /b 1
)

echo 1. Creating migrations...
docker exec -it tinisoft-backend python manage.py makemigrations

echo 2. Applying migrations...
docker exec -it tinisoft-backend python manage.py migrate

echo 3. Collecting static files...
docker exec -it tinisoft-backend python manage.py collectstatic --noinput

echo.
echo === Migration completed ===
echo.
echo Do you want to create a superuser? (y/n)
set /p response=
if "%response%"=="y" (
    docker exec -it tinisoft-backend python manage.py createsuperuser
)

pause

