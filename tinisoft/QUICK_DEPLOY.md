# Quick Deploy - Sunucuya İlk Kurulum

## Hızlı Adımlar

### 1. Sunucuya Bağlan
```bash
ssh user@your-server
```

### 2. Projeyi Klonla/Kopyala
```bash
cd /opt/projects
git clone <repo-url> tinisoft
cd tinisoft/tinisoft
```

### 3. Environment Ayarla
```bash
cp .env.example .env
nano .env  # SECRET_KEY, DB_PASSWORD, ALLOWED_HOSTS ayarla
```

### 4. Docker Compose ile Başlat
```bash
docker-compose up -d --build
```

### 5. Migration
```bash
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py createsuperuser
```

### 6. Nginx Yapılandır
```bash
sudo cp nginx.conf /etc/nginx/sites-available/tinisoft-api
sudo ln -s /etc/nginx/sites-available/tinisoft-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 7. SSL Sertifikası
```bash
sudo certbot --nginx -d api.tinisoft.com.tr
```

### 8. Test Et
```bash
curl https://api.tinisoft.com.tr/api/auth/register/
```

## Hızlı Komutlar

```bash
# Logları gör
docker-compose logs -f backend

# Container'ı yeniden başlat
docker-compose restart backend

# Migration yap
docker-compose exec backend python manage.py migrate

# Shell'e gir
docker-compose exec backend bash

# Database shell
docker-compose exec backend python manage.py dbshell
```

## Sorun Giderme

**Port çakışması:**
```bash
# Port'u değiştir docker-compose.yml'de
ports:
  - "127.0.0.1:8001:8000"  # 8000 yerine 8001
```

**Permission hatası:**
```bash
sudo chown -R $USER:$USER /opt/projects/tinisoft
```

**Database bağlantı hatası:**
```bash
# PostgreSQL'i kontrol et
docker-compose ps postgres
docker-compose logs postgres
```

