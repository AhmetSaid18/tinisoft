# 🚀 Hızlı Test Rehberi

## 1. Docker Container'ları Başlat

```bash
cd tinisoft
docker-compose up -d
```

## 2. Container Durumunu Kontrol Et

```bash
docker-compose ps
```

Tüm servislerin `Up` durumunda olduğundan emin ol.

## 3. Backend Loglarını İzle (Opsiyonel)

```bash
docker-compose logs -f backend
```

## 4. Test Scriptini Çalıştır

### Windows:
```bash
run_tests.bat
```

### Linux/Mac:
```bash
chmod +x run_tests.sh
./run_tests.sh
```

### Manuel (Container içinden):
```bash
docker exec -it tinisoft-backend python test_all_endpoints.py
```

### Manuel (Host'tan):
```bash
# requests yüklü olmalı
pip install requests

# Test scriptini çalıştır
python test_all_endpoints.py http://localhost:5000/api
```

## 5. Test Sonuçlarını Kontrol Et

Script şu testleri sırayla çalıştırır:
- ✅ Tenant Owner Kaydı
- ✅ Login
- ✅ Kategori Oluştur
- ✅ Ürün Oluştur
- ✅ Ürünleri Listele
- ✅ Ürün Detayı
- ✅ Tenant User Kaydı
- ✅ Tenant User Login
- ✅ Sepet Oluştur
- ✅ Sepete Ürün Ekle
- ✅ Sepeti Getir
- ✅ Ürün Ara
- ✅ Public Ürün Listesi
- ✅ Sadakat Programı

## 🔍 Sorun Giderme

### Backend başlamıyor
```bash
docker-compose logs backend
docker-compose restart backend
```

### Migration hataları
```bash
docker exec -it tinisoft-backend bash
python manage.py makemigrations
python manage.py migrate
```

### Port çakışması
`docker-compose.yml` dosyasındaki portları kontrol et:
- Backend: `localhost:5000` → `container:8000`
- PostgreSQL: `localhost:5433` → `container:5432`
- Redis: `localhost:6380` → `container:6379`

## 📊 Test Verileri

Her test çalıştırmasında:
- Yeni tenant oluşturulur (timestamp ile)
- Yeni ürünler ve kategoriler oluşturulur
- Test verileri birbirini etkilemez

## 🧹 Test Verilerini Temizle

```bash
# Tüm verileri sil (DİKKAT!)
docker-compose down -v
docker-compose up -d
```

