# Sunucuda Migration Oluşturma Komutları

## 📋 Sırasıyla Çalıştırılacak Komutlar

### 1. API Service (api-db)
```bash
docker-compose exec api dotnet ef migrations add InitialCreate --project /src/src/Tinisoft.Infrastructure --startup-project /src/src/Tinisoft.API --context ApplicationDbContext
```

### 2. Products API (products-db)
```bash
docker-compose exec products-api dotnet ef migrations add InitialCreate --project /src/src/Tinisoft.Infrastructure --startup-project /src/src/Tinisoft.Products.API --context ApplicationDbContext
```

### 3. Inventory API (inventory-db)
```bash
docker-compose exec inventory-api dotnet ef migrations add InitialCreate --project /src/src/Tinisoft.Infrastructure --startup-project /src/src/Tinisoft.Inventory.API --context ApplicationDbContext
```

### 4. Payments API (payments-db)
```bash
docker-compose exec payments-api dotnet ef migrations add InitialCreate --project /src/src/Tinisoft.Infrastructure --startup-project /src/src/Tinisoft.Payments.API --context ApplicationDbContext
```

### 5. Orders API (orders-db)
```bash
docker-compose exec orders-api dotnet ef migrations add InitialCreate --project /src/src/Tinisoft.Infrastructure --startup-project /src/src/Tinisoft.Orders.API --context ApplicationDbContext
```

### 6. Marketplace API (marketplace-db)
```bash
docker-compose exec marketplace-api dotnet ef migrations add InitialCreate --project /src/src/Tinisoft.Infrastructure --startup-project /src/src/Tinisoft.Marketplace.API --context ApplicationDbContext
```

### 7. Customers API (customers-db)
```bash
docker-compose exec customers-api dotnet ef migrations add InitialCreate --project /src/src/Tinisoft.Infrastructure --startup-project /src/src/Tinisoft.Customers.API --context ApplicationDbContext
```

### 8. Shipping API (shipping-db)
```bash
docker-compose exec shipping-api dotnet ef migrations add InitialCreate --project /src/src/Tinisoft.Infrastructure --startup-project /src/src/Tinisoft.Shipping.API --context ApplicationDbContext
```

### 9. Notifications API (notifications-db)
```bash
docker-compose exec notifications-api dotnet ef migrations add InitialCreate --project /src/src/Tinisoft.Infrastructure --startup-project /src/src/Tinisoft.Notifications.API --context ApplicationDbContext
```

### 10. Invoices API (invoices-db)
```bash
docker-compose exec invoices-api dotnet ef migrations add InitialCreate --src/src/Tinisoft.Infrastructure --startup-project /src/src/Tinisoft.Invoices.API --context ApplicationDbContext
```

---

## 🔄 Migration Dosyalarını Local'e Kopyalama

Migration'ları oluşturduktan sonra, dosyaları local'e kopyalamak için:

```bash
# API Service
docker cp tinisoft-api-1:/src/src/Tinisoft.Infrastructure/Persistence/Migrations/. ./src/Tinisoft.Infrastructure/Persistence/Migrations/

# Products API
docker cp tinisoft-products-api-1:/src/src/Tinisoft.Infrastructure/Persistence/Migrations/. ./src/Tinisoft.Infrastructure/Persistence/Migrations/

# Inventory API
docker cp tinisoft-inventory-api-1:/src/src/Tinisoft.Infrastructure/Persistence/Migrations/. ./src/Tinisoft.Infrastructure/Persistence/Migrations/

# Payments API
docker cp tinisoft-payments-api-1:/src/src/Tinisoft.Infrastructure/Persistence/Migrations/. ./src/Tinisoft.Infrastructure/Persistence/Migrations/

# Orders API
docker cp tinisoft-orders-api-1:/src/src/Tinisoft.Infrastructure/Persistence/Migrations/. ./src/Tinisoft.Infrastructure/Persistence/Migrations/

# Marketplace API
docker cp tinisoft-marketplace-api-1:/src/src/Tinisoft.Infrastructure/Persistence/Migrations/. ./src/Tinisoft.Infrastructure/Persistence/Migrations/

# Customers API
docker cp tinisoft-customers-api-1:/src/src/Tinisoft.Infrastructure/Persistence/Migrations/. ./src/Tinisoft.Infrastructure/Persistence/Migrations/

# Shipping API
docker cp tinisoft-shipping-api-1:/src/src/Tinisoft.Infrastructure/Persistence/Migrations/. ./src/Tinisoft.Infrastructure/Persistence/Migrations/

# Notifications API
docker cp tinisoft-notifications-api-1:/src/src/Tinisoft.Infrastructure/Persistence/Migrations/. ./src/Tinisoft.Infrastructure/Persistence/Migrations/

# Invoices API
docker cp tinisoft-invoices-api-1:/src/src/Tinisoft.Infrastructure/Persistence/Migrations/. ./src/Tinisoft.Infrastructure/Persistence/Migrations/
```

**VEYA** tüm container'ları tek seferde:

```bash
# Container isimlerini öğren
docker-compose ps

# Her container için migration dosyalarını kopyala
for container in $(docker-compose ps -q); do
    docker cp $container:/src/src/Tinisoft.Infrastructure/Persistence/Migrations/. ./src/Tinisoft.Infrastructure/Persistence/Migrations/ 2>/dev/null || true
done
```

---

## ✅ Sonraki Adımlar

1. Migration'ları oluştur (yukarıdaki komutlar)
2. Migration dosyalarını local'e kopyala
3. Git'e commit et:
   ```bash
   git add src/Tinisoft.Infrastructure/Persistence/Migrations/
   git commit -m "Add initial migrations for all services"
   git push
   ```
4. Artık sunucuda `docker-compose restart` yaptığında migration'lar otomatik uygulanacak!

---

## ⚠️ Not

Eğer container isimleri farklıysa (örneğin `tinisoft-api-1` yerine başka bir isim), önce container isimlerini kontrol et:

```bash
docker-compose ps
```

Sonra yukarıdaki komutlardaki container isimlerini güncelle.

