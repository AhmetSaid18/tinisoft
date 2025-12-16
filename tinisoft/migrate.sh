#!/bin/bash
# Migration script for Tinisoft

echo "=== Tinisoft Migration Script ==="

# Virtual environment kontrolü
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Virtual environment aktif et
echo "Activating virtual environment..."
source venv/bin/activate  # Linux/Mac
# Windows için: venv\Scripts\activate

# Dependencies yükle
echo "Installing dependencies..."
pip install -r requirements.txt

# Migration'ları oluştur
echo "Creating migrations..."
python manage.py makemigrations

# Migration'ları uygula
echo "Applying migrations..."
python manage.py migrate

# Superuser oluştur (opsiyonel)
echo "Do you want to create a superuser? (y/n)"
read -r response
if [ "$response" = "y" ]; then
    python manage.py createsuperuser
fi

echo "=== Migration completed ==="

