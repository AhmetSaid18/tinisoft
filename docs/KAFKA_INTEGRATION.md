# Kafka Entegrasyonu

## 🎯 Amaç

Büyük veri akışlarını (1000 tenant, 3M+ ürün) yönetmek için Kafka entegrasyonu eklendi. Hybrid yaklaşım kullanılıyor: **RabbitMQ** basit event'ler için, **Kafka** high-volume event'ler için.

## 📊 Mimari

### Event Routing Stratejisi

**Kafka'ya Giden Event'ler (High-Volume):**
- `ProductCreatedEvent`
- `ProductUpdatedEvent`
- `ProductDeletedEvent`
- `ProductStockChangedEvent`
- `OrderCreatedEvent`
- `OrderPaidEvent`
- `OrderStatusChangedEvent`

**RabbitMQ'ya Giden Event'ler (Basit/Low-Latency):**
- Diğer tüm event'ler (notification'lar, basit işlemler)

### Kafka Avantajları

1. **High Throughput**: Saniyede milyonlarca mesaj işleyebilir
2. **Event Replay**: Meilisearch index'i yeniden oluşturma, analytics için
3. **Partitioning**: Tenant bazlı partition (her tenant'ın event'leri aynı partition'da)
4. **Consumer Groups**: Paralel işleme (birden fazla consumer instance)
5. **Durability**: Event'ler kaybolmaz, 7 gün retention

## 🔧 Konfigürasyon

### appsettings.json

```json
{
  "Kafka": {
    "BootstrapServers": "localhost:9092",
    "TopicPrefix": "tinisoft",
    "ConsumerGroup": "tinisoft-consumers"
  },
  "RabbitMQ": {
    "HostName": "localhost",
    "Port": "5672",
    "UserName": "guest",
    "Password": "guest",
    "ExchangeName": "tinisoft_events"
  }
}
```

### Docker Compose

Kafka ve Zookeeper otomatik olarak başlatılır:

```bash
docker-compose up -d
```

## 📦 Kafka Topics

Otomatik oluşturulan topic'ler:

- `tinisoft.products` - Product event'leri
- `tinisoft.orders` - Order event'leri
- `tinisoft.inventory` - Stock/Inventory event'leri
- `tinisoft.events` - Default topic (diğer event'ler)

Her topic **3 partition** ile oluşturulur (tenant bazlı load balancing için).

## 🔄 Consumer İşlemleri

`KafkaConsumerService` (Background Service) şu işlemleri yapar:

1. **Product Events**:
   - `ProductDeletedEvent` → Meilisearch'ten sil
   - `ProductCreatedEvent` / `ProductUpdatedEvent` → Log (Meilisearch zaten handler'da index ediyor)

2. **Stock Events**:
   - `ProductStockChangedEvent` → Cache invalidation (product cache'i temizle)

3. **Order Events**:
   - Log (ileride analytics, notification için kullanılabilir)

## 🚀 Kullanım

Kod değişikliği **gerekmez**. Mevcut `IEventBus` kullanımı aynı kalır:

```csharp
await _eventBus.PublishAsync(new ProductCreatedEvent
{
    ProductId = product.Id,
    TenantId = tenantId,
    Title = product.Title,
    SKU = product.SKU
}, cancellationToken);
```

`HybridEventBus` otomatik olarak event'i doğru yere yönlendirir.

## 📈 Performans

### Kafka Producer Ayarları

- **Compression**: Snappy (yüksek throughput)
- **Batch Size**: 16KB
- **Linger**: 10ms (batch için bekleme)
- **Idempotence**: Enabled (duplicate önleme)
- **Acks**: All (tüm replica'ların onayı)

### Kafka Consumer Ayarları

- **Auto Offset Reset**: Earliest (ilk mesajdan başla)
- **Enable Auto Commit**: False (manuel commit - işlem başarılı olursa commit)
- **Max Poll Interval**: 5 dakika

## 🔍 Monitoring

### Kafka Topics Kontrol

```bash
# Kafka container'a gir
docker exec -it tinisoft-kafka-1 bash

# Topic'leri listele
kafka-topics --bootstrap-server localhost:9092 --list

# Topic detayları
kafka-topics --bootstrap-server localhost:9092 --describe --topic tinisoft.products

# Consumer group durumu
kafka-consumer-groups --bootstrap-server localhost:9092 --group tinisoft-consumers --describe
```

### Log Monitoring

Consumer işlemleri log'lanır:

```
[Information] Event published to Kafka: ProductCreatedEvent - {EventId} to topic tinisoft.products partition 0 offset 12345
[Information] Product created event received: ProductId: {ProductId}, TenantId: {TenantId}
```

## 🎯 Senaryolar

### Senaryo 1: 1000 Tenant, Her Biri 1000 Ürün

**Kafka ile:**
- Product event'leri Kafka'ya gider
- Partitioning sayesinde load dağıtılır
- Consumer'lar paralel işler
- Meilisearch indexing background'da yapılır
- **Sonuç**: Sistem stabil, performans yüksek

### Senaryo 2: Cold Start (Cache Boş)

**Kafka ile:**
- Event'ler Kafka'da saklanır (7 gün)
- İhtiyaç halinde replay edilebilir
- Meilisearch index'i yeniden oluşturulabilir
- **Sonuç**: Data kaybı yok, recovery mümkün

### Senaryo 3: Meilisearch Index Yeniden Oluşturma

```bash
# Kafka'dan tüm product event'lerini replay et
# (İleride implement edilecek)
```

## 🔐 Güvenlik

Production'da:

1. **SASL/SSL**: Kafka'ya authentication ekle
2. **ACLs**: Topic'lere erişim kontrolü
3. **Encryption**: Mesaj şifreleme (TLS)

## 📝 Notlar

- Kafka **opsiyonel**: Sadece `Kafka:BootstrapServers` set edilirse aktif olur
- RabbitMQ **fallback**: Kafka yoksa RabbitMQ kullanılır
- **Hybrid mode**: Her ikisi de varsa otomatik routing yapılır
- Consumer **background service**: Uygulama başladığında otomatik çalışır

## 🐛 Troubleshooting

### Kafka bağlantı hatası

```
Error: Kafka producer error: Connection refused
```

**Çözüm**: Kafka container'ının çalıştığından emin ol:
```bash
docker-compose ps kafka
```

### Consumer mesaj işlemiyor

**Kontrol**:
1. Consumer group durumunu kontrol et
2. Log'larda hata var mı bak
3. Topic'te mesaj var mı kontrol et

### Partition imbalance

**Çözüm**: TenantId bazlı partition key kullanılıyor, bu normal. İhtiyaç halinde partition sayısını artır.

