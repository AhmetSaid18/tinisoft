@echo off
REM API Test Script Runner (Windows)
REM Docker container'da testleri çalıştırır

echo ==========================================
echo Tinisoft API Test Script
echo ==========================================
echo.

REM Docker container'ın çalışıp çalışmadığını kontrol et
docker ps | findstr tinisoft-backend >nul
if errorlevel 1 (
    echo [ERROR] Backend container çalışmıyor!
    echo Önce 'docker-compose up -d' ile container'ları başlatın.
    exit /b 1
)

echo [OK] Backend container çalışıyor
echo.

REM Test scriptini container içinde çalıştır
echo Test scripti çalıştırılıyor...
echo.

docker exec -it tinisoft-backend python test_all_endpoints.py

echo.
echo ==========================================
echo Test tamamlandı!
echo ==========================================
pause

