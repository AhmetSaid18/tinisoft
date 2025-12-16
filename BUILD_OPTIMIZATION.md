# Docker Build Optimizasyonu

## 🐌 Mevcut Durum
- Her servis için ~9 dakika build süresi
- Toplam ~90 dakika (paralel olmasa)
- İlk build'de cache yok

## ⚡ Optimizasyonlar

### 1. Paralel Build (Hızlı Çözüm)
```bash
# Tüm servisleri paralel build et
docker-compose build --parallel

# Veya sadece değişen servisleri rebuild et
docker-compose build --no-cache api payments-api
```

### 2. Sadece Değişen Servisleri Rebuild Et
```bash
# Sadece API servisini rebuild et
docker-compose build api

# Sadece Payments API'yi rebuild et
docker-compose build payments-api
```

### 3. Cache Kullanımı
İkinci build'den itibaren cache sayesinde çok daha hızlı olacak:
- İlk build: ~9 dakika/servis
- İkinci build (cache ile): ~1-2 dakika/servis (sadece değişen kısımlar)

### 4. Sadece Gerekli Servisleri Build Et
```bash
# Sadece belirli servisleri build et
docker-compose build api payments-api orders-api

# Sonra tümünü başlat
docker-compose up -d
```

## 📊 Beklenen Süreler

### İlk Build (Cache Yok)
- **Paralel olmadan**: ~90 dakika (10 servis x 9 dakika)
- **Paralel ile**: ~15-20 dakika (tüm servisler aynı anda)

### İkinci Build (Cache Var)
- **Paralel olmadan**: ~10-15 dakika
- **Paralel ile**: ~2-3 dakika

### Sadece Kod Değişikliği (Cache Var)
- **Paralel olmadan**: ~5-10 dakika
- **Paralel ile**: ~1-2 dakika

## 🚀 Önerilen Workflow

### İlk Build (Sunucuda)
```bash
# Tüm servisleri paralel build et
docker-compose build --parallel

# Sonra başlat
docker-compose up -d
```

### Kod Değişikliği Sonrası
```bash
# Sadece değişen servisleri rebuild et
docker-compose build --no-cache api  # Örnek: sadece API değişti

# Sonra restart
docker-compose restart api
```

### Hızlı Test İçin
```bash
# Sadece test etmek istediğin servisi rebuild et
docker-compose build payments-api
docker-compose up -d payments-api
```

## ⚠️ Notlar

1. **İlk build uzun sürer** - Bu normal! Cache oluşuyor.
2. **Sonraki build'ler hızlı** - Cache sayesinde sadece değişen kısımlar rebuild edilir.
3. **Paralel build kullan** - `--parallel` flag'i ile tüm servisler aynı anda build edilir.
4. **.dockerignore eklendi** - Gereksiz dosyalar artık kopyalanmıyor.

## 🔧 Daha Fazla Optimizasyon İstersen

Eğer hala çok yavaşsa, şunları yapabiliriz:
1. Multi-stage build optimizasyonu
2. Ortak dependency'leri ayrı bir base image'a çıkarma
3. BuildKit kullanımı (Docker 20.10+)

Ama şu an için `.dockerignore` ve paralel build yeterli olmalı.

