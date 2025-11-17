# Cold Start Optimization Guide

## Senaryo
- 1000 tenant
- Her tenant'ta 1000 resimli ürün
- Toplam: 1,000,000 ürün
- Cold start (cache boş)
- Aynı anda hepsine istek

## Yapılması Gerekenler

### 1. PostgreSQL Configuration

```sql
-- max_connections artır (default 100)
ALTER SYSTEM SET max_connections = 300;
SELECT pg_reload_conf();

-- shared_buffers artır (RAM'in %25'i)
ALTER SYSTEM SET shared_buffers = '4GB';

-- effective_cache_size artır (RAM'in %50-75'i)
ALTER SYSTEM SET effective_cache_size = '12GB';

-- work_mem artır (her connection için)
ALTER SYSTEM SET work_mem = '64MB';

-- max_worker_processes artır
ALTER SYSTEM SET max_worker_processes = 8;
```

### 2. Connection String

```json
{
  "ConnectionStrings": {
    "DefaultConnection": "Host=localhost;Port=5432;Database=tinisoft;Username=postgres;Password=postgres;MinPoolSize=50;MaxPoolSize=200;Connection Lifetime=0;Command Timeout=30;Timeout=30;Pooling=true"
  }
}
```

### 3. Database Index'leri

Tüm kritik index'ler zaten var:
- `IX_Product_TenantId_IsActive_CreatedAt`
- `IX_Product_TenantId_Title`
- `IX_Product_TenantId_SKU`
- `IX_Product_TenantId_Price`

### 4. Monitoring

- Database connection pool kullanımı
- Query execution time
- Circuit breaker durumu
- Cache hit rate

### 5. Horizontal Scaling (İleride)

- Read replicas (okuma yükü için)
- API servislerini scale et
- Load balancer

## Beklenen Performans

**Cold Start (ilk 1-2 saniye):**
- İlk query: ~100-300ms (database'den)
- Connection pool: 200 connection → 200 tenant paralel
- Queue: 800 tenant bekler (normal)

**Cache doldukça:**
- Sonraki query: ~10-50ms (cache'den)
- Performans artar

**Circuit Breaker:**
- 200 failure sonra devreye girer
- Database'i korur
- 30 saniye sonra tekrar dener

## Sonuç

✅ Sistem bu senaryoyu kaldırabilir
✅ Circuit breaker database'i korur
✅ Cache doldukça performans artar
✅ Graceful degradation

