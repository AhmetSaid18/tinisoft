# Migration Oluşturma Rehberi

## Otomatik Uygulama
✅ Migration'lar **otomatik uygulanıyor** - Docker container'lar başladığında `RunMigrations: "true"` sayesinde var olan migration'lar veritabanına uygulanıyor.

## Manuel Oluşturma
❌ Migration dosyalarını **oluşturmak** için local'de manuel komut çalıştırman gerekiyor.

### Her Servis İçin Migration Oluşturma

#### 1. API Service (Ana servis - api-db)
```powershell
dotnet ef migrations add MigrationName --project src/Tinisoft.Infrastructure --startup-project src/Tinisoft.API --context ApplicationDbContext
```

#### 2. Products API (products-db)
```powershell
dotnet ef migrations add MigrationName --project src/Tinisoft.Infrastructure --startup-project src/Tinisoft.Products.API --context ApplicationDbContext
```

#### 3. Inventory API (inventory-db)
```powershell
dotnet ef migrations add MigrationName --project src/Tinisoft.Infrastructure --startup-project src/Tinisoft.Inventory.API --context ApplicationDbContext
```

#### 4. Payments API (payments-db)
```powershell
dotnet ef migrations add MigrationName --project src/Tinisoft.Infrastructure --startup-project src/Tinisoft.Payments.API --context ApplicationDbContext
```

#### 5. Orders API (orders-db)
```powershell
dotnet ef migrations add MigrationName --project src/Tinisoft.Infrastructure --startup-project src/Tinisoft.Orders.API --context ApplicationDbContext
```

#### 6. Marketplace API (marketplace-db)
```powershell
dotnet ef migrations add MigrationName --project src/Tinisoft.Infrastructure --startup-project src/Tinisoft.Marketplace.API --context ApplicationDbContext
```

#### 7. Customers API (customers-db)
```powershell
dotnet ef migrations add MigrationName --project src/Tinisoft.Infrastructure --startup-project src/Tinisoft.Customers.API --context ApplicationDbContext
```

#### 8. Shipping API (shipping-db)
```powershell
dotnet ef migrations add MigrationName --project src/Tinisoft.Infrastructure --startup-project src/Tinisoft.Shipping.API --context ApplicationDbContext
```

#### 9. Notifications API (notifications-db)
```powershell
dotnet ef migrations add MigrationName --project src/Tinisoft.Infrastructure --startup-project src/Tinisoft.Notifications.API --context ApplicationDbContext
```

#### 10. Invoices API (invoices-db)
```powershell
dotnet ef migrations add MigrationName --project src/Tinisoft.Infrastructure --startup-project src/Tinisoft.Invoices.API --context ApplicationDbContext
```

## Önemli Notlar

1. **Migration dosyaları oluşturulduktan sonra Git'e commit edilmeli** - Böylece sunucuda da aynı migration'lar olur
2. **Sunucuda migration'lar otomatik uygulanır** - `RunMigrations: "true"` sayesinde container başladığında migration'lar uygulanır
3. **Her servis kendi veritabanına sahip** - Her servis için ayrı migration oluşturulmalı
4. **Migration isimleri açıklayıcı olmalı** - Örnek: `AddPaymentProvider`, `UpdateOrderStatus`, `AddTenantContactEmail`

## Örnek Workflow

1. Entity'de değişiklik yap (örn: `PaymentProvider` entity'sine yeni property ekle)
2. Local'de migration oluştur:
   ```powershell
   dotnet ef migrations add AddPaymentProviderSettings --project src/Tinisoft.Infrastructure --startup-project src/Tinisoft.Payments.API --context ApplicationDbContext
   ```
3. Migration dosyalarını kontrol et (`src/Tinisoft.Infrastructure/Persistence/Migrations/`)
4. Git'e commit et
5. Sunucuda `docker-compose up -d` çalıştır - Migration'lar otomatik uygulanır

