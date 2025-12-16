# Tinisoft Deployment Guide

## Sunucuya Deployment

### 1. Sunucuya Dosyaları Yükle

```bash
# Git ile
git clone <repo-url> /opt/projects/tinisoft
cd /opt/projects/tinisoft/tinisoft

# Veya SCP ile
scp -r tinisoft/ user@server:/opt/projects/tinisoft/
```

### 2. Environment Variables Ayarla

```bash
# .env dosyasını oluştur
cp .env.example .env
nano .env
```

**Önemli değişkenler:**
```env
SECRET_KEY=your-very-secret-key-here
DEBUG=False
ALLOWED_HOSTS=api.tinisoft.com.tr
DB_PASSWORD=strong-password-here
```

### 3. Docker Compose ile Deploy

```bash
# Build ve start
docker-compose up -d --build

# Logları kontrol et
docker-compose logs -f backend
```

### 4. Migration Yap

```bash
# Migration'ları uygula
docker-compose exec backend python manage.py migrate

# Superuser oluştur (opsiyonel)
docker-compose exec backend python manage.py createsuperuser
```

### 5. Static Files

```bash
# Static files topla
docker-compose exec backend python manage.py collectstatic --noinput
```

### 6. Nginx/Traefik Yapılandırması

**Nginx örneği:**
```nginx
server {
    listen 80;
    server_name api.tinisoft.com.tr;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /static/ {
        alias /opt/projects/tinisoft/tinisoft/staticfiles/;
    }
    
    location /media/ {
        alias /opt/projects/tinisoft/tinisoft/media/;
    }
}
```

**SSL için Let's Encrypt:**
```bash
certbot --nginx -d api.tinisoft.com.tr
```

### 7. Health Check

```bash
# API health check
curl https://api.tinisoft.com.tr/api/auth/register/

# Container durumları
docker-compose ps
```

## Production Checklist

- [ ] `.env` dosyası oluşturuldu ve güvenli
- [ ] `SECRET_KEY` güçlü ve unique
- [ ] `DEBUG=False`
- [ ] `ALLOWED_HOSTS` doğru ayarlandı
- [ ] Database şifresi güçlü
- [ ] SSL sertifikası yapılandırıldı
- [ ] Static files toplandı
- [ ] Migration'lar uygulandı
- [ ] Celery worker çalışıyor
- [ ] Loglar kontrol edildi
- [ ] Backup stratejisi hazır

## Troubleshooting

### Migration Hatası
```bash
# Schema oluştur
docker-compose exec postgres psql -U postgres -d tinisoft -c "CREATE SCHEMA IF NOT EXISTS public;"

# Migration tekrar dene
docker-compose exec backend python manage.py migrate
```

### Container Başlamıyor
```bash
# Logları kontrol et
docker-compose logs backend

# Container'ı yeniden başlat
docker-compose restart backend
```

### Database Bağlantı Hatası
```bash
# PostgreSQL durumunu kontrol et
docker-compose ps postgres

# Bağlantıyı test et
docker-compose exec backend python manage.py dbshell
```

## Update Deployment

```bash
# Git'ten çek
git pull

# Rebuild
docker-compose up -d --build

# Migration
docker-compose exec backend python manage.py migrate

# Restart
docker-compose restart backend celery celery-beat
```

