# Database Architecture - Multi-Tenant Schema Structure

## Tek PostgreSQL Veritabanı Yapısı

### Public Schema (Sistem Tabloları)
- `users` - Tüm kullanıcılar (Owner, TenantUser, TenantBayii)
- `tenants` - Tüm tenant'lar (mağazalar)
- `domains` - Tüm domain kayıtları
- Django sistem tabloları (auth, admin, sessions, vb.)

### Tenant Schemas (Her Tenant İçin)
Her tenant için ayrı schema: `tenant_{tenant_id}`

**Örnek:** `tenant_abc123` schema'sında:
- `products` - Ürünler
- `categories` - Kategoriler
- `orders` - Siparişler
- `shipping` - Kargo bilgileri
- `inventory` - Stok bilgileri
- `customers` - Müşteriler (TenantUser'lar)
- `payments` - Ödemeler
- `invoices` - Faturalar
- vb.

## Nasıl Çalışır?

### 1. Request Geldiğinde
```
Request: https://example.com/products
→ TenantMiddleware domain'den tenant bulur
→ set_tenant_schema('tenant_abc123')
```

### 2. Database Router
```
Product.objects.all()
→ TenantDatabaseRouter
→ tenant_abc123 schema'sına yönlendir
→ SELECT * FROM tenant_abc123.products
```

### 3. Tenant İzolasyonu
- Her tenant'ın verileri kendi schema'sında
- Tenant A'nın products'ı → `tenant_a.products`
- Tenant B'nin products'ı → `tenant_b.products`
- Tam izolasyon, veri karışmaz

## Model Yapısı

### Tenant-Specific Modeller
```python
# apps/models/product.py
class Product(BaseModel):
    tenant = models.ForeignKey('Tenant', ...)  # Tenant ilişkisi
    name = models.CharField(...)
    price = models.DecimalField(...)
    
    class Meta:
        db_table = 'products'
        # Tenant schema'sında oluşturulur
```

### Sistem Modelleri (Public Schema)
```python
# apps/models/auth.py
class Tenant(BaseModel):
    # Public schema'da
    name = models.CharField(...)
    
    class Meta:
        db_table = 'tenants'
```

## Avantajlar

✅ **Tek DB Yönetimi** - Kolay backup, migration
✅ **Tam İzolasyon** - Schema seviyesinde güvenlik
✅ **Performans** - Index'ler schema bazlı
✅ **Ölçeklenebilirlik** - Yeni tenant = yeni schema
✅ **Migration Kolaylığı** - Her tenant için ayrı migration

## Migration Süreci

### 1. İlk Migration (Public Schema)
```bash
python manage.py makemigrations
python manage.py migrate
# → Public schema'ya tablolar oluşturulur
```

### 2. Tenant Schema Migration
```python
# Tenant oluşturulduğunda
create_tenant_schema('tenant_abc123')
# → Schema oluşturulur

# Tenant-specific modeller için migration
set_tenant_schema('tenant_abc123')
python manage.py migrate
# → tenant_abc123 schema'sına tablolar oluşturulur
```

## Örnek: Product Modeli

```python
# apps/models/product.py
from core.models import BaseModel

class Product(BaseModel):
    """
    Tenant-specific product modeli.
    Her tenant'ın kendi schema'sında products tablosu olur.
    """
    tenant = models.ForeignKey(
        'Tenant',
        on_delete=models.CASCADE,
        related_name='products'
    )
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_places=2, decimal_places=2)
    # ...
    
    class Meta:
        db_table = 'products'
        # Tenant schema'sında oluşturulur
```

## Sorun Olur mu?

**HAYIR!** Çünkü:

1. ✅ **Schema İzolasyonu** - Her tenant'ın verileri ayrı schema'da
2. ✅ **Automatic Routing** - Database router otomatik yönlendirir
3. ✅ **Migration Support** - Her schema için ayrı migration
4. ✅ **Performance** - Index'ler schema bazlı, hızlı sorgular
5. ✅ **Scalability** - Yeni tenant = yeni schema, kolay ekleme

## Önemli Notlar

- Tenant-specific modellerde `tenant` ForeignKey zorunlu
- Public schema modellerinde `tenant` yok
- Migration'lar schema-aware olmalı
- Database router doğru çalışmalı

