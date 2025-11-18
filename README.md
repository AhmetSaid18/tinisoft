# Tinisoft - Multi-Tenant E-Commerce SaaS Backend

ASP.NET Core 8 REST API backend for multi-tenant e-commerce SaaS platform (Shopify/İdeasoft tarzı).

## 🏗️ Mimari

**Microservices Architecture** - Her servis ayrı container, ayrı database, event-driven communication:

### Microservices
- **Tinisoft.Products.API** - Ürün yönetimi servisi (Port: 5001)
- **Tinisoft.Inventory.API** - Stok yönetimi servisi (Port: 5002)
- **Tinisoft.Payments.API** - Ödeme işlemleri servisi (Port: 5003)
- **Tinisoft.Orders.API** - Sipariş yönetimi servisi (Port: 5004)
- **Tinisoft.Marketplace.API** - Marketplace entegrasyonları (Port: 5005)
- **Tinisoft.Customers.API** - Müşteri yönetimi servisi (Port: 5006)
- **Tinisoft.Shipping.API** - Kargo entegrasyonları servisi (Port: 5007)
- **Tinisoft.Notifications.API** - Email/SMS bildirimleri servisi (Port: 5008)
- **Tinisoft.API.Gateway** - API Gateway (Ocelot) - Tüm istekleri yönlendirir (Port: 5000)

### Infrastructure
- **PostgreSQL** - Her servis kendi database'ine sahip (Database per Service)
- **Redis** - Cache (Port: 6380)
- **RabbitMQ** - Event Bus (Port: 5672, Management: 15672)
- **Kafka** - High-volume event streaming (Port: 9092)
- **Zookeeper** - Kafka için (Port: 2181)

## 🚀 Hızlı Başlangıç

### 1. Environment Variables Ayarlama

```bash
# .env.example dosyasını .env olarak kopyala
cp .env.example .env

# .env dosyasını düzenle ve tüm değerleri doldur
nano .env
```

**Önemli**: `.env` dosyası asla Git'e commit edilmemeli! (`.gitignore`'da zaten var)

### 2. Docker Compose ile Başlatma

```bash
docker-compose up -d
```

### 3. Health Check

```bash
docker-compose ps
```

Tüm servislerin `Up` durumunda olduğunu kontrol edin.

### 4. API Gateway'e Erişim

- **API Gateway**: `http://localhost:5000`
- **Swagger UI**: `http://localhost:5000/swagger` (Development)

## 📋 Port Yapılandırması

Sunucudaki mevcut portlarla çakışmayı önlemek için portlar özelleştirilmiştir:

| Servis | Port | Açıklama |
|--------|------|----------|
| Gateway | 5000 | API Gateway |
| Products API | 5001 | Ürün servisi |
| Inventory API | 5002 | Stok servisi |
| Payments API | 5003 | Ödeme servisi |
| Orders API | 5004 | Sipariş servisi |
| Marketplace API | 5005 | Marketplace servisi |
| Customers API | 5006 | Müşteri servisi |
| Shipping API | 5007 | Kargo servisi |
| Notifications API | 5008 | Bildirim servisi |
| Products DB | 6000 | Products database |
| Inventory DB | 6001 | Inventory database |
| Payments DB | 6002 | Payments database |
| Orders DB | 6003 | Orders database |
| Marketplace DB | 6004 | Marketplace database |
| Customers DB | 6005 | Customers database |
| Shipping DB | 6006 | Shipping database |
| Notifications DB | 6007 | Notifications database |
| Redis | 6380 | Cache |
| RabbitMQ | 5672 | Event Bus |
| RabbitMQ Management | 15672 | Management UI |
| Kafka | 9092 | Event Streaming |
| Zookeeper | 2181 | Kafka coordination |

**Not**: Port çakışması durumunda `.env` dosyasında ilgili port değişkenini değiştirebilirsiniz.

## 🔐 Güvenlik

### Environment Variables

Tüm hassas bilgiler `.env` dosyasında tutulur:

- Database şifreleri
- JWT secret key
- SMTP ayarları
- API key'ler (Kargo firmaları, PayTR, vb.)
- RabbitMQ şifreleri

**Asla `.env` dosyasını Git'e commit etmeyin!**

### JWT Authentication

- JWT token tabanlı authentication
- Role-based authorization (SystemAdmin, TenantAdmin, Customer)
- Token expiration: 24 saat (varsayılan)

## 📚 Özellikler

- ✅ **Multi-Tenant Architecture** - Finbuckle.MultiTenant ile tenant izolasyonu
- ✅ **CQRS Pattern** - MediatR ile command/query ayrımı
- ✅ **PostgreSQL** - EF Core 8 ile veritabanı
- ✅ **Redis** - Cache ve rate limiting
- ✅ **Hangfire** - Background job processing
- ✅ **Meilisearch** - Hızlı ürün arama
- ✅ **RabbitMQ/Kafka** - Event-driven architecture
- ✅ **Kargo Entegrasyonları** - Aras, MNG, Yurtiçi Kargo
- ✅ **Email Bildirimleri** - SMTP ile email gönderimi
- ✅ **PayTR Integration** - Ödeme entegrasyonu
- ✅ **Audit Logging** - Tüm işlemlerin loglanması
- ✅ **Health Checks** - Sistem sağlık kontrolü
- ✅ **Swagger** - API dokümantasyonu

## 🔄 Event-Driven Architecture

- **RabbitMQ Event Bus**: Servisler arası asenkron iletişim
- **Kafka**: High-volume event streaming
- **Domain Events**: ProductCreated, OrderCreated, OrderPaid, vb.
- **Event Exchange**: `tinisoft_events` (Topic Exchange)

## 📖 API Dokümantasyonu

Development ortamında Swagger UI:
- `http://localhost:5000/swagger`

## 🐳 Docker Compose Yapısı

Her servis ayrı container olarak çalışır:

```yaml
services:
  products-api      # Ürün servisi
  inventory-api     # Stok servisi
  payments-api      # Ödeme servisi
  orders-api        # Sipariş servisi
  marketplace-api   # Marketplace servisi
  customers-api     # Müşteri servisi
  shipping-api      # Kargo servisi
  notifications-api # Bildirim servisi
  gateway           # API Gateway
  products-db       # Products database
  inventory-db      # Inventory database
  # ... diğer database'ler
  rabbitmq          # Event Bus
  redis             # Cache
  kafka             # Event Streaming
  zookeeper         # Kafka coordination
```

## 📊 Database per Service Pattern

Her microservice kendi database'ine sahip:
- **products-db**: Sadece ürün verileri
- **inventory-db**: Sadece stok verileri
- **payments-db**: Sadece ödeme verileri
- **orders-db**: Sadece sipariş verileri
- **marketplace-db**: Sadece marketplace verileri
- **customers-db**: Sadece müşteri verileri
- **shipping-db**: Sadece kargo verileri
- **notifications-db**: Sadece bildirim verileri

Servisler arası iletişim **RabbitMQ/Kafka Events** ile yapılır.

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

## 📝 Deployment

Detaylı deployment bilgileri için [DEPLOYMENT.md](DEPLOYMENT.md) dosyasına bakın.

## 📄 Lisans

Proprietary
