# Sunucuda Migration Çalıştırma Rehberi

## ✅ Otomatik Migration Sistemi

Sistem **tamamen otomatik** çalışıyor! Migration dosyalarını Git'e commit ettiğinde, sunucuda container'lar başladığında otomatik olarak uygulanacak.

## 🔄 Sunucuda Yapılacaklar

### 1. Git'ten Güncellemeleri Çek
```bash
cd /path/to/tinisoft
git pull origin main  # veya master
```

### 2. Docker Container'ları Yeniden Başlat
```bash
docker-compose down
docker-compose up -d --build
```

**VEYA** sadece restart:
```bash
docker-compose restart
```

### 3. Migration'lar Otomatik Uygulanacak! 🎉

Her servis başlarken:
- `RunMigrations: "true"` kontrolü yapılır
- `Program.cs`'deki migration kodu çalışır
- `dbContext.Database.MigrateAsync()` ile migration'lar uygulanır
- Log'larda "Database migrations applied successfully" mesajını görürsün

## 📋 Hangi Servislerde Migration Var?

Tüm servislerde otomatik migration aktif:

1. ✅ **api** (api-db) - `RunMigrations: "true"`
2. ✅ **products-api** (products-db) - `RunMigrations: "true"`
3. ✅ **inventory-api** (inventory-db) - `RunMigrations: "true"`
4. ✅ **payments-api** (payments-db) - `RunMigrations: "true"`
5. ✅ **orders-api** (orders-db) - `RunMigrations: "true"`
6. ✅ **marketplace-api** (marketplace-db) - `RunMigrations: "true"`
7. ✅ **customers-api** (customers-db) - `RunMigrations: "true"`
8. ✅ **shipping-api** (shipping-db) - `RunMigrations: "true"`
9. ✅ **notifications-api** (notifications-db) - `RunMigrations: "true"`
10. ✅ **invoices-api** (invoices-db) - `RunMigrations: "true"`

## 🔍 Migration Loglarını Kontrol Et

```bash
# Tüm servislerin loglarını kontrol et
docker-compose logs | grep -i migration

# Belirli bir servisin loglarını kontrol et
docker-compose logs api | grep -i migration
docker-compose logs payments-api | grep -i migration
```

## ⚠️ Önemli Notlar

1. **Migration dosyaları Git'te olmalı** - Eğer migration dosyalarını Git'e commit etmediysen, sunucuda migration'lar uygulanmaz
2. **İlk kez çalıştırıyorsan** - `docker-compose up -d --build` kullan (image'ları yeniden build eder)
3. **Sadece restart yeterli** - Migration dosyaları zaten image içindeyse, sadece `docker-compose restart` yeterli
4. **Hata durumunda** - Log'larda hata mesajı görürsün, container durmaz (sadece log'lar)

## 🚀 Örnek Sunucu Workflow

```bash
# 1. Git'ten çek
git pull origin main

# 2. Container'ları yeniden başlat
docker-compose down
docker-compose up -d --build

# 3. Log'ları kontrol et (migration'ların uygulandığını gör)
docker-compose logs api | tail -20
docker-compose logs payments-api | tail -20

# 4. Servislerin sağlığını kontrol et
docker-compose ps
```

## 📝 Migration Dosyaları Nerede?

Migration dosyaları şu dizinde:
```
src/Tinisoft.Infrastructure/Persistence/Migrations/
```

Bu dosyalar Docker image'ına build sırasında kopyalanır, bu yüzden Git'e commit edilmiş olmalılar.

