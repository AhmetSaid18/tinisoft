# API Test Rehberi

Bu rehber, Docker'da çalışan sistemi test etmek için adım adım talimatlar içerir.

## 🚀 Hızlı Başlangıç

### 1. Docker Container'ları Başlat

```bash
cd tinisoft
docker-compose up -d
```

### 2. Container'ların Durumunu Kontrol Et

```bash
docker-compose ps
```

Tüm servislerin `Up` durumunda olduğundan emin ol:
- `tinisoft-postgres` - PostgreSQL
- `tinisoft-redis` - Redis
- `tinisoft-backend` - Django Backend
- `tinisoft-celery` - Celery Worker
- `tinisoft-celery-beat` - Celery Beat

### 3. Backend Loglarını Kontrol Et

```bash
docker-compose logs -f backend
```

Migration'ların başarılı olduğundan ve server'ın başladığından emin ol.

### 4. Test Scriptini Çalıştır

#### Seçenek 1: Docker Container İçinden

```bash
# Backend container'a gir
docker exec -it tinisoft-backend bash

# Test scriptini çalıştır
python test_all_endpoints.py
```

#### Seçenek 2: Host'tan (localhost)

```bash
# requests kütüphanesini yükle (eğer yoksa)
pip install requests

# Test scriptini çalıştır
cd tinisoft
python test_all_endpoints.py http://localhost:5000/api
```

## 📋 Test Senaryosu

Test scripti şu adımları sırayla test eder:

1. ✅ **Tenant Owner Kaydı** - Yeni bir mağaza sahibi kaydı
2. ✅ **Login** - Token al
3. ✅ **Kategori Oluştur** - Yeni kategori ekle
4. ✅ **Ürün Oluştur** - Yeni ürün ekle
5. ✅ **Ürünleri Listele** - Tüm ürünleri getir
6. ✅ **Ürün Detayı** - Tek ürün detayını getir
7. ✅ **Tenant User Kaydı** - Müşteri kaydı
8. ✅ **Tenant User Login** - Müşteri girişi
9. ✅ **Sepet Oluştur** - Yeni sepet
10. ✅ **Sepete Ürün Ekle** - Ürün ekle
11. ✅ **Sepeti Getir** - Sepet bilgilerini al
12. ✅ **Ürün Ara** - Arama yap
13. ✅ **Public Ürün Listesi** - Public endpoint test
14. ✅ **Sadakat Programı** - Loyalty program yönetimi

## 🔍 Manuel Test (Postman/cURL)

### 1. Tenant Owner Kaydı

```bash
curl -X POST http://localhost:5000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test123456!",
    "first_name": "Test",
    "last_name": "Owner",
    "store_name": "Test Store",
    "store_slug": "test-store"
  }'
```

### 2. Login

```bash
curl -X POST http://localhost:5000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test123456!"
  }'
```

Response'dan `token` al ve sonraki isteklerde kullan:

```bash
TOKEN="your-token-here"
```

### 3. Ürün Oluştur

```bash
curl -X POST http://localhost:5000/api/products/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "name": "Test Ürün",
    "slug": "test-urun",
    "description": "Test açıklama",
    "price": "100.00",
    "status": "active",
    "is_visible": true
  }'
```

### 4. Ürünleri Listele

```bash
curl -X GET http://localhost:5000/api/products/ \
  -H "Authorization: Bearer $TOKEN"
```

### 5. Public Ürün Listesi (Token gerekmez)

```bash
curl -X GET http://localhost:5000/api/public/products/
```

## 🐛 Sorun Giderme

### Backend başlamıyor

```bash
# Logları kontrol et
docker-compose logs backend

# Container'ı yeniden başlat
docker-compose restart backend
```

### Migration hataları

```bash
# Container içine gir
docker exec -it tinisoft-backend bash

# Migration'ları manuel çalıştır
python manage.py makemigrations
python manage.py migrate
```

### Database bağlantı hatası

```bash
# PostgreSQL'in çalıştığını kontrol et
docker-compose ps postgres

# Database'e bağlanmayı dene
docker exec -it tinisoft-postgres psql -U postgres -d tinisoft
```

### Port çakışması

`docker-compose.yml` dosyasındaki portları kontrol et:
- Backend: `5000:8000` (localhost:5000 → container:8000)
- PostgreSQL: `5433:5432`
- Redis: `6380:6379`

## 📊 Test Sonuçları

Test scripti çalıştıktan sonra:
- ✅ Başarılı testler yeşil işaretle gösterilir
- ❌ Başarısız testler kırmızı işaretle gösterilir
- ⚠️ Atlanan testler sarı işaretle gösterilir

## 🔄 Test Verilerini Temizle

Test verilerini temizlemek için:

```bash
# Database'i sıfırla (DİKKAT: Tüm veriler silinir!)
docker-compose down -v
docker-compose up -d
```

## 📝 Notlar

- Test scripti her çalıştırmada yeni tenant ve ürünler oluşturur
- Timestamp kullanıldığı için aynı testler tekrar çalıştırılabilir
- Token'lar test süresince geçerlidir
- Session bazlı endpoint'ler (cart) için session cookie gerekebilir

