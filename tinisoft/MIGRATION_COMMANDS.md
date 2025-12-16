# Migration Komutları - Container İçinde

## İlk Migration (Container Çalışırken)

### 1. Container'a Gir
```bash
docker exec -it tinisoft-backend bash
```

### 2. Migration Oluştur (İlk Kez)
```bash
python manage.py makemigrations
```

### 3. Migration Uygula
```bash
python manage.py migrate
```

### 4. Superuser Oluştur (Opsiyonel)
```bash
python manage.py createsuperuser
```

### 5. Container'tan Çık
```bash
exit
```

## Tek Komutla (Container Dışından)

### Migration Uygula
```bash
docker exec -it tinisoft-backend python manage.py migrate
```

### Superuser Oluştur
```bash
docker exec -it tinisoft-backend python manage.py createsuperuser
```

### Migration Oluştur
```bash
docker exec -it tinisoft-backend python manage.py makemigrations
```

## Yeni Model Eklendiğinde

```bash
# 1. Migration oluştur
docker exec -it tinisoft-backend python manage.py makemigrations

# 2. Migration uygula
docker exec -it tinisoft-backend python manage.py migrate
```

## Hızlı Komutlar

```bash
# Migration durumunu kontrol et
docker exec -it tinisoft-backend python manage.py showmigrations

# Belirli bir app için migration
docker exec -it tinisoft-backend python manage.py makemigrations apps

# Migration geri al (son migration'ı geri al)
docker exec -it tinisoft-backend python manage.py migrate apps zero
```

## Sorun Giderme

### Migration Hatası
```bash
# Container loglarını kontrol et
docker logs tinisoft-backend

# Database bağlantısını test et
docker exec -it tinisoft-backend python manage.py dbshell
```

### Schema Oluşturma
```bash
# PostgreSQL container'a gir
docker exec -it tinisoft-postgres psql -U postgres -d tinisoft

# Schema oluştur (gerekirse)
CREATE SCHEMA IF NOT EXISTS public;
\q
```

