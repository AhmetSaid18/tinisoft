# 🚨 Hızlı Migration Çözümü

## Sorun
`Users` tablosu yok hatası alıyorsun. Migration dosyaları henüz oluşturulmamış.

## ✅ Çözüm: Container İçinde Migration Oluştur

Artık container'larda `dotnet ef` tool'u var! Migration dosyalarını container içinde oluşturabilirsin.

---

## 📋 Adım Adım

### 1. Container İçinde Migration Dosyalarını Oluştur

```bash
# API servisi için migration oluştur
docker exec -it tinisoft-api-1 dotnet ef migrations add InitialCreate \
    --project /src/src/Tinisoft.Infrastructure \
    --context ApplicationDbContext \
    --startup-project /src/src/Tinisoft.API
```

### 2. Migration Dosyalarını Container'dan Çıkar

```bash
# Migration dosyalarını container'dan host'a kopyala
docker cp tinisoft-api-1:/src/src/Tinisoft.Infrastructure/Persistence/Migrations ./temp-migrations

# Git'e ekle
cp -r ./temp-migrations/* src/Tinisoft.Infrastructure/Persistence/Migrations/
git add src/Tinisoft.Infrastructure/Persistence/Migrations/
git commit -m "Add initial database migrations"
git push
```

### 3. Migration'ları Çalıştır

```bash
# API için
docker exec -it tinisoft-api-1 dotnet ef database update \
    --project /src/src/Tinisoft.Infrastructure \
    --context ApplicationDbContext

# Veya helper script ile
./scripts/migrate.sh api
```

---

## 🎯 Tek Komutla (Hızlı Test İçin)

Eğer sadece test ediyorsan ve Git'e commit etmeyeceksen:

```bash
# Migration oluştur ve çalıştır (container içinde kalır)
docker exec -it tinisoft-api-1 bash -c "
    cd /src/src/Tinisoft.API && \
    dotnet ef migrations add InitialCreate \
        --project ../Tinisoft.Infrastructure \
        --context ApplicationDbContext \
        --startup-project . && \
    dotnet ef database update \
        --project ../Tinisoft.Infrastructure \
        --context ApplicationDbContext \
        --startup-project .
"
```

**Not:** Bu migration dosyaları container içinde kalır, Git'e commit edilmez. Production için yukarıdaki adımları takip et.

---

## 🔄 Tüm Servisler İçin

Her servis için aynı işlemi tekrarla:

```bash
# Products API
docker exec -it tinisoft-products-api-1 dotnet ef migrations add InitialCreate \
    --project /src/src/Tinisoft.Infrastructure \
    --context ApplicationDbContext \
    --startup-project /src/src/Tinisoft.Products.API

# Orders API
docker exec -it tinisoft-orders-api-1 dotnet ef migrations add InitialCreate \
    --project /src/src/Tinisoft.Infrastructure \
    --context ApplicationDbContext \
    --startup-project /src/src/Tinisoft.Orders.API

# ... diğer servisler için de aynı
```

---

## ⚠️ Önemli

- Migration dosyaları Git'te olmalı (production için)
- Her servis aynı migration dosyalarını kullanır (ama farklı database'lere uygular)
- İlk migration'ı oluşturduktan sonra Git'e commit et!

---

## 🔧 PostgreSQL Filter Syntax Hatası Düzeltme

Eğer migration çalıştırırken `syntax error at or near "["` hatası alıyorsan:

### Hızlı Çözüm: Migration Dosyasını Düzelt

```bash
# 1. Önce migration dosyalarının yerini bul
docker exec -it tinisoft-api-1 find /src/src/Tinisoft.Infrastructure -name "*InitialCreate*.cs" -type f

# 2. Migration dosyalarını container'dan çıkar (bulduğun yola göre)
# Genellikle /src/src/Tinisoft.Infrastructure/Migrations/ altında olur
docker cp tinisoft-api-1:/src/src/Tinisoft.Infrastructure/Migrations ./temp-migrations

# 3. Migration dosyasını düzelt (SQL Server syntax'ını PostgreSQL'e çevir)
# Dosyada [GIBInvoiceId], [SKU], [CustomerId], [IpAddress] gibi köşeli parantezleri kaldır
sed -i 's/\[GIBInvoiceId\]/GIBInvoiceId/g' ./temp-migrations/*InitialCreate*.cs
sed -i 's/\[SKU\]/SKU/g' ./temp-migrations/*InitialCreate*.cs
sed -i 's/\[CustomerId\]/CustomerId/g' ./temp-migrations/*InitialCreate*.cs
sed -i 's/\[IpAddress\]/IpAddress/g' ./temp-migrations/*InitialCreate*.cs

# 4. Düzeltilmiş dosyayı container'a geri kopyala
docker cp ./temp-migrations tinisoft-api-1:/src/src/Tinisoft.Infrastructure/Migrations

# 5. Database'i güncelle
docker exec -it tinisoft-api-1 bash -c "
    cd /src/src/Tinisoft.API && \
    dotnet ef database update \
        --project ../Tinisoft.Infrastructure \
        --context ApplicationDbContext \
        --startup-project .
"
```

**VEYA Container İçinde Direkt Düzelt (ÖNERİLEN):**

```bash
# Container içinde direkt düzelt
# PostgreSQL'de WHERE clause'da kolon isimlerini tırnak içine almamız gerekiyor
docker exec -it tinisoft-api-1 bash -c "
    cd /src/src/Tinisoft.Infrastructure/Migrations && \
    sed -i 's/WHERE GIBInvoiceId IS NOT NULL/WHERE \"GIBInvoiceId\" IS NOT NULL/g' *InitialCreate*.cs && \
    sed -i 's/WHERE SKU IS NOT NULL/WHERE \"SKU\" IS NOT NULL/g' *InitialCreate*.cs && \
    sed -i 's/WHERE CustomerId IS NOT NULL/WHERE \"CustomerId\" IS NOT NULL/g' *InitialCreate*.cs && \
    sed -i 's/WHERE IpAddress IS NOT NULL/WHERE \"IpAddress\" IS NOT NULL/g' *InitialCreate*.cs && \
    echo 'Migration dosyaları düzeltildi!'
"
```

### Alternatif: Migration'ı Sil ve Yeniden Oluştur

```bash
# 1. Migration'ı sil
docker exec -it tinisoft-api-1 bash -c "
    cd /src/src/Tinisoft.API && \
    dotnet ef migrations remove \
        --project ../Tinisoft.Infrastructure \
        --context ApplicationDbContext \
        --startup-project . \
        --force
"

# 2. Container'ı yeniden build et (yeni kodları yükle)
# docker-compose build tinisoft-api
# docker-compose up -d tinisoft-api

# 3. Migration'ı yeniden oluştur
docker exec -it tinisoft-api-1 bash -c "
    cd /src/src/Tinisoft.API && \
    dotnet ef migrations add InitialCreate \
        --project ../Tinisoft.Infrastructure \
        --context ApplicationDbContext \
        --startup-project .
"

# 4. Database'i güncelle
docker exec -it tinisoft-api-1 bash -c "
    cd /src/src/Tinisoft.API && \
    dotnet ef database update \
        --project ../Tinisoft.Infrastructure \
        --context ApplicationDbContext \
        --startup-project .
"
```

