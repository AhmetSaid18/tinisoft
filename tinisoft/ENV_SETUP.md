# Environment Variables Setup

## Hızlı Kurulum

```bash
# .env dosyasını oluştur
cp env.example .env

# Düzenle
nano .env
```

## Zorunlu Değişkenler

### 1. SECRET_KEY
```bash
# Django secret key oluştur
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```
Çıktıyı `SECRET_KEY=` değerine yapıştır.

### 2. DB_PASSWORD
Güçlü bir database şifresi kullan:
```bash
# Örnek (değiştir!)
DB_PASSWORD=MyStr0ng!P@ssw0rd123
```

### 3. ALLOWED_HOSTS
Production için:
```bash
ALLOWED_HOSTS=api.tinisoft.com.tr
```

Development için:
```bash
ALLOWED_HOSTS=localhost,127.0.0.1
```

## Önemli Notlar

- ✅ `.env` dosyasını **ASLA** Git'e commit etme!
- ✅ Production'da `DEBUG=False` olmalı
- ✅ `SECRET_KEY` güçlü ve unique olmalı
- ✅ Database şifresi güçlü olmalı
- ✅ SSL sertifikası için `SECURE_SSL_REDIRECT=True`

## Environment Variables Açıklamaları

### Django Core
- `SECRET_KEY`: Django secret key (zorunlu)
- `DEBUG`: Debug mode (production'da False)
- `ALLOWED_HOSTS`: İzin verilen host'lar (virgülle ayrılmış)

### Database
- `DB_NAME`: PostgreSQL database adı
- `DB_USER`: PostgreSQL kullanıcı adı
- `DB_PASSWORD`: PostgreSQL şifresi (zorunlu)
- `DB_HOST`: PostgreSQL host (Docker'da: postgres)
- `DB_SCHEMA`: Default schema (public)

### Redis & Celery
- `REDIS_HOST`: Redis host (Docker'da: redis)
- `CELERY_BROKER_URL`: Celery broker URL
- `CELERY_RESULT_BACKEND`: Celery result backend

### Domain Management
- `DOMAIN_VERIFICATION_TXT_PREFIX`: DNS TXT record prefix
- `DOMAIN_VERIFICATION_CNAME_TARGET`: DNS CNAME target

### Email
- `EMAIL_HOST`: SMTP server
- `EMAIL_HOST_USER`: Email kullanıcı adı
- `EMAIL_HOST_PASSWORD`: Email şifresi (app password)

## Production Checklist

- [ ] `SECRET_KEY` oluşturuldu ve güçlü
- [ ] `DEBUG=False`
- [ ] `ALLOWED_HOSTS` doğru ayarlandı
- [ ] `DB_PASSWORD` güçlü
- [ ] Email ayarları yapılandırıldı
- [ ] SSL ayarları aktif (`SECURE_SSL_REDIRECT=True`)

