@echo off
REM Migration script for Tinisoft (Windows)

echo === Tinisoft Migration Script ===

REM Virtual environment kontrolü
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Virtual environment aktif et
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Dependencies yükle
echo Installing dependencies...
pip install -r requirements.txt

REM Migration'ları oluştur
echo Creating migrations...
python manage.py makemigrations

REM Migration'ları uygula
echo Applying migrations...
python manage.py migrate

REM Superuser oluştur (opsiyonel)
echo Do you want to create a superuser? (y/n)
set /p response=
if "%response%"=="y" (
    python manage.py createsuperuser
)

echo === Migration completed ===
pause

