# Tinisoft - Multi-Tenant E-Commerce SaaS Backend

ASP.NET Core 8 REST API backend for multi-tenant e-commerce SaaS platform (Shopify/İdeasoft tarzı).

## 🏗️ Mimari

**Microservices Architecture** - Her servis ayrı container, ayrı database, event-driven communication:

### Microservices
- **Tinisoft.Products.API** - Ürün yönetimi servisi (Port: 5001)
- **Tinisoft.Inventory.API** - Stok yönetimi servisi (Port: 5002)
- **Tinisoft.Payments.API** - Ödeme işlemleri servisi (Port: 5003)
- **Tinisoft.API.Gateway** - API Gateway (Ocelot) - Tüm istekleri yönlendirir (Port: 5000)

### Shared Katmanlar
- **Tinisoft.Application** - CQRS (MediatR), Commands/Queries
- **Tinisoft.Domain** - Entities, Value Objects, Domain Interfaces
- **Tinisoft.Infrastructure** - EF Core, PostgreSQL, Redis, RabbitMQ, R2 Storage, PayTR
- **Tinisoft.Shared** - Events, Contracts, Event Bus Interface

### Infrastructure
- **RabbitMQ** - Event Bus (Servisler arası iletişim)
- **PostgreSQL** - Her servis kendi database'ine sahip (Database per Service)
- **Redis** - Cache
- **Ocelot** - API Gateway

## 🚀 Özellikler

- ✅ **Multi-Tenant Architecture** - Finbuckle.MultiTenant ile tenant izolasyonu
- ✅ **CQRS Pattern** - MediatR ile command/query ayrımı
- ✅ **PostgreSQL** - EF Core 8 ile veritabanı
- ✅ **Redis** - Cache ve rate limiting
- ✅ **Hangfire** - Background job processing
- ✅ **Meilisearch** - Hızlı ürün arama
- ✅ **Cloudflare R2** - S3-compatible object storage
- ✅ **PayTR Integration** - Ödeme entegrasyonu
- ✅ **Audit Logging** - Tüm işlemlerin loglanması
- ✅ **Health Checks** - Sistem sağlık kontrolü
- ✅ **Swagger** - API dokümantasyonu

## 📋 Gereksinimler

- .NET 8.0 SDK
- PostgreSQL 14+
- Redis (opsiyonel)
- Meilisearch (opsiyonel)

## 🔧 Kurulum

### Docker Compose ile Çalıştırma (Önerilen)

Tüm microservices'i tek komutla başlat:

```bash
docker-compose up -d
```

Bu komut şunları başlatır:
- **3 PostgreSQL Database** (products-db, inventory-db, payments-db)
- **Redis** (Cache)
- **RabbitMQ** (Event Bus)
- **Products API** (Port: 5001)
- **Inventory API** (Port: 5002)
- **Payments API** (Port: 5003)
- **API Gateway** (Port: 5000)

### Servis URL'leri

- **API Gateway**: `http://localhost:5000`
- **Products API**: `http://localhost:5001`
- **Inventory API**: `http://localhost:5002`
- **Payments API**: `http://localhost:5003`
- **RabbitMQ Management**: `http://localhost:15672` (guest/guest)

### API Gateway Üzerinden İstekler

Tüm istekler API Gateway üzerinden yapılır:

```bash
# Products
GET http://localhost:5000/api/products
POST http://localhost:5000/api/products

# Inventory
GET http://localhost:5000/api/inventory/products/{productId}
POST http://localhost:5000/api/inventory/adjust

# Payments
POST http://localhost:5000/api/payments/process
```

### Manuel Çalıştırma

Her servisi ayrı ayrı çalıştırmak için:

```bash
# Products API
cd src/Tinisoft.Products.API
dotnet run

# Inventory API
cd src/Tinisoft.Inventory.API
dotnet run

# Payments API
cd src/Tinisoft.Payments.API
dotnet run

# API Gateway
cd src/Tinisoft.API.Gateway
dotnet run
```

## 📚 API Dokümantasyonu

Development ortamında Swagger UI:
- `https://localhost:5001/swagger`

## 🏢 Multi-Tenant Yapı

Tenant çözümleme:
- **Host Strategy**: `www.marka.com` → domains tablosundan tenant_id bulur
- **Header Strategy**: `X-Tenant-Id` header'ı ile tenant belirtilir
- **Slug Strategy**: `tenant.tinisoft.com` formatında slug'dan tenant bulur

Her sorguda tenant guard aktif - `ITenantEntity` implement eden entity'ler otomatik filtrelenir.

## 📦 Proje Yapısı

```
src/
├── Tinisoft.API/              # API Layer
│   ├── Controllers/          # Products, Inventory, Payments
│   ├── Middleware/
│   └── Program.cs
├── Tinisoft.Application/      # Application Layer (CQRS)
│   ├── Products/             # Ürün modülü
│   │   ├── Commands/         # Create, Update, Delete
│   │   └── Queries/          # Get, List
│   ├── Inventory/            # Stok yönetimi modülü
│   │   ├── Commands/         # AdjustStock
│   │   └── Queries/          # GetStockLevel
│   ├── Payments/             # Ödeme modülü
│   │   └── Commands/         # ProcessPayment, VerifyPayment
│   └── Common/
│       ├── Behaviours/       # MediatR pipeline behaviours
│       └── Mappings/         # AutoMapper profiles
├── Tinisoft.Domain/           # Domain Layer
│   ├── Entities/             # Product, Order, Tenant, etc.
│   └── Common/
├── Tinisoft.Infrastructure/   # Infrastructure Layer
│   ├── Persistence/           # EF Core, DbContext
│   ├── MultiTenant/           # Finbuckle configuration
│   └── Services/              # External services (R2, PayTR, etc.)
└── Tinisoft.Shared/          # Shared Contracts
    ├── Events/                # Domain events (ProductCreated, OrderPaid, etc.)
    └── Contracts/              # IEventBus (RabbitMQ/Kafka için hazır)
```

## 🎯 Modüler Yapı

### Products Modülü
- ✅ **CRUD İşlemleri**: Create, Read, Update, Delete
- ✅ **Listeleme**: Pagination, Search, Filter, Sort
- ✅ **Event Publishing**: ProductCreated, ProductUpdated, ProductDeleted
- ✅ **Kategori Yönetimi**: Ürün-kategori ilişkileri

### Inventory Modülü
- ✅ **Stok Takibi**: Product ve Variant seviyesinde
- ✅ **Stok Ayarlama**: Restock, Sale, Adjustment, Return
- ✅ **Stok Sorgulama**: Gerçek zamanlı stok seviyesi
- ✅ **Event Publishing**: ProductStockChanged

### Payments Modülü
- ✅ **Ödeme İşleme**: PayTR entegrasyonu
- ✅ **Ödeme Doğrulama**: Callback verification
- ✅ **Modüler Tasarım**: İleride Stripe, Iyzico, vb. eklenebilir
- ✅ **Event Publishing**: OrderPaid

## 🔄 Event-Driven Architecture

- **RabbitMQ Event Bus**: Servisler arası asenkron iletişim
- **Domain Events**: ProductCreated, ProductUpdated, ProductStockChanged, OrderPaid, etc.
- **Event Exchange**: `tinisoft_events` (Topic Exchange)
- **Servisler bağımsız**: Her servis kendi database'ine sahip ve bağımsız deploy edilebilir

## 🔐 Güvenlik

- Tenant izolasyonu (EF Core global query filters)
- CORS yapılandırması
- Audit logging
- Rate limiting (Redis ile - eklenecek)

## 📝 Notlar

- Frontend ve proxy yönetimi bu projede yok - sadece backend API
- Domain bağlama ve SSL yönetimi reverse proxy (Caddy/Nginx) tarafında yapılmalı
- Storefront rendering frontend (Next.js) tarafında yapılacak

## 🛠️ Geliştirme

### Yeni Entity Ekleme

1. `Tinisoft.Domain/Entities/` altına entity ekle
2. `ITenantEntity` implement et (eğer tenant-specific ise)
3. `ApplicationDbContext`'e DbSet ekle
4. Migration oluştur: `dotnet ef migrations add AddNewEntity`

### Yeni API Endpoint Ekleme

1. `Tinisoft.Application/[Module]/` altına Command/Query ekle (CQRS)
2. `Tinisoft.API/Controllers/` altına controller ekle
3. MediatR ile command/query çağır

### Yeni Modül Ekleme

1. `Tinisoft.Application/[ModuleName]/` klasörü oluştur
2. Commands ve Queries ekle
3. İlgili controller'ı `Tinisoft.API/Controllers/` altına ekle
4. Event'leri `Tinisoft.Shared/Events/` altına ekle (gerekirse)

## 🐳 Docker Compose Yapısı

Her servis ayrı container olarak çalışır:

```yaml
services:
  products-api      # Ürün servisi
  inventory-api     # Stok servisi
  payments-api      # Ödeme servisi
  gateway           # API Gateway
  products-db       # Products database
  inventory-db      # Inventory database
  payments-db       # Payments database
  rabbitmq          # Event Bus
  redis             # Cache
```

## 📊 Database per Service Pattern

Her microservice kendi database'ine sahip:
- **products-db**: Sadece ürün verileri
- **inventory-db**: Sadece stok verileri
- **payments-db**: Sadece ödeme verileri

Servisler arası iletişim **RabbitMQ Events** ile yapılır.

## 📄 Lisans

Proprietary
