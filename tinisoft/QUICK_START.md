# Tinisoft Quick Start Guide

## 1. Migration Yapma

### Windows:
```bash
migrate.bat
```

### Linux/Mac:
```bash
chmod +x migrate.sh
./migrate.sh
```

### Manuel:
```bash
# Virtual environment oluştur
python -m venv venv

# Aktif et
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Dependencies yükle
pip install -r requirements.txt

# Migration oluştur
python manage.py makemigrations

# Migration uygula
python manage.py migrate

# Superuser oluştur (opsiyonel)
python manage.py createsuperuser
```

## 2. Server Çalıştırma

```bash
python manage.py runserver
```

## 3. Postman Collection

1. Postman'i aç
2. Import → File seç
3. `Tinisoft_API.postman_collection.json` dosyasını seç
4. Environment variables ayarla:
   - `base_url`: `https://api.tinisoft.com.tr`
   - `tenant_slug`: `my-store`

## 4. İlk Test

1. **Register (Owner)** endpoint'ini çağır
2. Response'dan `domain_id` al
3. DNS kaydını ekle (TXT veya CNAME)
4. **Verify Domain** endpoint'ini çağır
5. **Domain Status** ile kontrol et

## 5. Environment Variables

`.env` dosyasını düzenle:
```env
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=api.tinisoft.com.tr
DB_NAME=tinisoft
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=postgres
DB_PORT=5432
```

