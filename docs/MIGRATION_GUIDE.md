# 🚀 Production Migration Guide

## Django'daki `python manage.py migrate` Gibi Kullanım

Artık container içinde `dotnet ef database update` komutunu çalıştırabilirsin!

---

## 📋 Migration Çalıştırma

### Tek Bir Servis İçin

```bash
# API servisi için
docker exec -it tinisoft-api-1 dotnet ef database update --project /src/src/Tinisoft.Infrastructure --context ApplicationDbContext

# Products API için
docker exec -it tinisoft-products-api-1 dotnet ef database update --project /src/src/Tinisoft.Infrastructure --context ApplicationDbContext

# Orders API için
docker exec -it tinisoft-orders-api-1 dotnet ef database update --project /src/src/Tinisoft.Infrastructure --context ApplicationDbContext

# Diğer servisler için de aynı pattern
```

### Tüm Servisler İçin (Toplu)

```bash
# Tüm API servisleri için migration çalıştır
docker exec -it tinisoft-api-1 dotnet ef database update --project /src/src/Tinisoft.Infrastructure --context ApplicationDbContext
docker exec -it tinisoft-products-api-1 dotnet ef database update --project /src/src/Tinisoft.Infrastructure --context ApplicationDbContext
docker exec -it tinisoft-orders-api-1 dotnet ef database update --project /src/src/Tinisoft.Infrastructure --context ApplicationDbContext
docker exec -it tinisoft-inventory-api-1 dotnet ef database update --project /src/src/Tinisoft.Infrastructure --context ApplicationDbContext
docker exec -it tinisoft-customers-api-1 dotnet ef database update --project /src/src/Tinisoft.Infrastructure --context ApplicationDbContext
docker exec -it tinisoft-payments-api-1 dotnet ef database update --project /src/src/Tinisoft.Infrastructure --context ApplicationDbContext
docker exec -it tinisoft-marketplace-api-1 dotnet ef database update --project /src/src/Tinisoft.Infrastructure --context ApplicationDbContext
docker exec -it tinisoft-shipping-api-1 dotnet ef database update --project /src/src/Tinisoft.Infrastructure --context ApplicationDbContext
docker exec -it tinisoft-notifications-api-1 dotnet ef database update --project /src/src/Tinisoft.Infrastructure --context ApplicationDbContext
docker exec -it tinisoft-invoices-api-1 dotnet ef database update --project /src/src/Tinisoft.Infrastructure --context ApplicationDbContext
```

---

## 🔧 Migration Oluşturma (Local'de)

Migration dosyalarını oluşturmak için local'de şu komutları çalıştır:

```bash
# API için
cd src/Tinisoft.API
dotnet ef migrations add InitialCreate --project ../Tinisoft.Infrastructure --context ApplicationDbContext

# Products API için
cd src/Tinisoft.Products.API
dotnet ef migrations add InitialCreate --project ../Tinisoft.Infrastructure --context ApplicationDbContext

# ... diğer servisler için de aynı
```

**Önemli:** Migration dosyalarını Git'e commit et!

```bash
git add src/Tinisoft.Infrastructure/Persistence/Migrations/
git commit -m "Add database migrations"
git push
```

---

## ✅ Otomatik Migration (Program.cs)

`RunMigrations=true` environment variable'ı ile container başlarken otomatik migration çalışır:

```yaml
# docker-compose.yml
api:
  environment:
    RunMigrations: "true"
```

---

## 🎯 Özet

1. **Migration Oluşturma:** Local'de `dotnet ef migrations add` → Git'e commit
2. **Migration Çalıştırma:** Container'da `dotnet ef database update` (Django'daki `python manage.py migrate` gibi)
3. **Otomatik Migration:** `RunMigrations=true` ile container başlarken otomatik çalışır

---

## 📝 Notlar

- Container'larda artık `dotnet ef` tool'u mevcut
- Migration dosyaları Git'te olmalı (container'a kopyalanır)
- Her servis kendi database'ine sahip, her biri için ayrı migration çalıştırılmalı
- Production'da `RunMigrations=true` kullanarak otomatik migration yapabilirsin

