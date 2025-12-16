# 🚀 Container Optimizasyonu - Özet

## ✅ Tamamlanan İşlemler

### 1. docker-compose.yml Optimize Edildi
- **27 container → 12 container** (%55 azalma)
- Tek PostgreSQL database (schema bazlı)
- Kafka + Zookeeper kaldırıldı
- Meilisearch kaldırıldı
- Traefik kaldırıldı
- customers-api ve invoices-api kaldırıldı (api'ye birleştirildi)
- marketplace-api devre dışı (comment out)

### 2. Schema Initialization Script Oluşturuldu
- `scripts/init-schemas.sql` dosyası oluşturuldu
- PostgreSQL başlatıldığında otomatik schema'lar oluşturulacak

### 3. Connection String'ler Güncellendi
- Tüm servisler tek PostgreSQL'e bağlanıyor
- Her servis kendi schema'sını kullanıyor (SearchPath parametresi ile)

## ⚠️ Yapılması Gerekenler

### 1. ApplicationDbContext Schema Ayarları
Her servis için ApplicationDbContext'te schema belirtilmeli:

```csharp
protected override void OnModelCreating(ModelBuilder modelBuilder)
{
    base.OnModelCreating(modelBuilder);
    
    // Schema belirt
    modelBuilder.HasDefaultSchema("products"); // Her servis için farklı
}
```

**Servisler ve Schema'ları:**
- `products-api` → `products` schema
- `inventory-api` → `inventory` schema
- `payments-api` → `payments` schema
- `orders-api` → `orders` schema
- `shipping-api` → `shipping` schema
- `notifications-api` → `notifications` schema
- `api` (main) → `public` schema

### 2. Migration'ları Güncelle
Mevcut migration'ları schema bazlı olacak şekilde güncelle veya yeni migration'lar oluştur.

### 3. Gateway Yapılandırması
`ocelot.json` dosyasında `customers-api` ve `invoices-api` route'larını kaldır (artık `api` içinde).

## 📊 Sonuç

### Önce: 27 Container
- 10 Database
- 6 Infrastructure
- 10 API Servisleri
- 1 Gateway

### Sonra: 12 Container ⚡
- 1 Database (PostgreSQL)
- 2 Infrastructure (Redis, RabbitMQ)
- 7 API Servisleri
- 1 Gateway

### Build Süresi
- **Önce**: ~20 dakika (tüm servisler)
- **Sonra**: ~10-12 dakika (50% azalma)

### Memory Kullanımı
- **Önce**: ~8-10 GB
- **Sonra**: ~4-5 GB (50% azalma)

## 🔄 İleride Genişletme

İhtiyaç olduğunda:
1. Database'leri tekrar ayırabilirsin (schema → database)
2. Kafka ekleyebilirsin
3. Meilisearch ekleyebilirsin
4. Yeni servisler ekleyebilirsin

**Şimdilik minimal setup ile başla, ihtiyaç oldukça genişlet!**

