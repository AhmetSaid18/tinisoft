# SKU Bazlı Varyant Sistemi - Kullanım Kılavuzu

## 📋 Genel Bakış

Bu sistem, "ana ürün" kavramı olmadan, SKU bazlı otomatik varyant gruplama sağlar. Aynı `variant_group_sku` değerine sahip ürünler otomatik olarak birbirlerinin varyantı olarak kabul edilir.

## 🔧 Sistem Özellikleri

### ✅ Avantajlar
- **Basitlik**: Her ürün bağımsız bir Product nesnesi
- **Esneklik**: SKU ile otomatik gruplama
- **Production-Ready**: Karmaşık ilişkiler yok
- **Kolay Sorgulama**: Basit filtrelerle varyantları bulabilirsin

## 📊 Model Değişiklikleri

### Product Modeli
```python
class Product(BaseModel):
    # ... mevcut fieldlar ...
    
    variant_group_sku = models.CharField(
        max_length=200,
        blank=True,
        db_index=True
    )
```

## 🎯 Kullanım Örnekleri

### 1. Varyantlı Ürün Oluşturma

**Senaryo**: 3 farklı renkli T-Shirt oluşturmak istiyorsun.

```json
// Ürün 1: Kırmızı T-Shirt
POST /api/products/
{
  "name": "Premium T-Shirt - Kırmızı",
  "slug": "premium-tshirt-kirmizi",
  "sku": "TSHIRT-RED-M",
  "variant_group_sku": "TSHIRT-001",  // ← Varyant grubu
  "price": 199.99,
  "inventory_quantity": 50
}

// Ürün 2: Mavi T-Shirt
POST /api/products/
{
  "name": "Premium T-Shirt - Mavi",
  "slug": "premium-tshirt-mavi",
  "sku": "TSHIRT-BLUE-M",
  "variant_group_sku": "TSHIRT-001",  // ← Aynı grup
  "price": 199.99,
  "inventory_quantity": 30
}

// Ürün 3: Yeşil T-Shirt
POST /api/products/
{
  "name": "Premium T-Shirt - Yeşil",
  "slug": "premium-tshirt-yesil",
  "sku": "TSHIRT-GREEN-M",
  "variant_group_sku": "TSHIRT-001",  // ← Aynı grup
  "price": 199.99,
  "inventory_quantity": 20
}
```

### 2. API Response

**Ürün Detayını Çekince:**

```json
GET /api/products/{id}/

{
  "id": 1,
  "name": "Premium T-Shirt - Kırmızı",
  "sku": "TSHIRT-RED-M",
  "variant_group_sku": "TSHIRT-001",
  "price": "199.99",
  // ... diğer fieldlar ...
  
  // ← Otomatik olarak varyantlar geliyor
  "variant_group_products": [
    {
      "id": 2,
      "name": "Premium T-Shirt - Mavi",
      "slug": "premium-tshirt-mavi",
      "price": "199.99",
      "sku": "TSHIRT-BLUE-M",
      "inventory_quantity": 30,
      "is_in_stock": true
    },
    {
      "id": 3,
      "name": "Premium T-Shirt - Yeşil",
      "slug": "premium-tshirt-yesil",
      "price": "199.99",
      "sku": "TSHIRT-GREEN-M",
      "inventory_quantity": 20,
      "is_in_stock": true
    }
  ]
}
```

## 🎨 Frontend Entegrasyonu

### Ürün Listesi
```javascript
// Ürün kartlarında varyant olup olmadığını kontrol et
const hasVariants = product.variant_group_products && 
                    product.variant_group_products.length > 0;

if (hasVariants) {
  // "3 varyant mevcut" gibi bir badge göster
  console.log(`${product.variant_group_products.length + 1} varyant mevcut`);
}
```

### Ürün Detay Sayfası
```javascript
// Varyant seçici göster
if (product.variant_group_products.length > 0) {
  const allVariants = [
    // Mevcut ürün
    {
      id: product.id,
      name: product.name,
      slug: product.slug,
      price: product.price
    },
    // Diğer varyantlar
    ...product.variant_group_products
  ];
  
  // Seçici render et
  renderVariantSelector(allVariants);
}
```

## 🔍 Backend Filtreleme

### Varyant Grubu Ürünlerini Listeleme
```python
# Aynı variant_group_sku'ya sahip tüm ürünleri getir
variants = Product.objects.filter(
    tenant=tenant,
    variant_group_sku="TSHIRT-001",
    is_deleted=False,
    status='active'
)
```

### Varyant Olmayan Ürünleri Filtreleme
```python
# Sadece varyant grubu olmayan ürünleri getir
standalone_products = Product.objects.filter(
    tenant=tenant,
    variant_group_sku='',  # veya None
    is_deleted=False,
    status='active'
)
```

## 📝 Best Practices

### 1. SKU Şeması Tutarlılığı
```
Format: {PRODUCT_CODE}-{VARIANT_ATTR}-{SIZE}

Örnekler:
- TSHIRT-001: Varyant grubu
- TSHIRT-RED-M: Kırmızı, M beden
- TSHIRT-BLUE-L: Mavi, L beden
```

### 2. Varyant İsimlendirme
```
Ana ürün adı + Varyant özelliği

Doğru: "Premium T-Shirt - Kırmızı"
Yanlış: "Kırmızı Premium T-Shirt"
```

### 3. Fiyatlandırma
```python
# Varyantlar farklı fiyatlara sahip olabilir
{
  "variant_group_sku": "SHOE-001",
  "name": "Spor Ayakkabı - 42 Numara",
  "price": 499.99  # Farklı numaralar farklı fiyatlar
}
```

## 🚀 Migration Sonrası

Migration'ı çalıştırdıktan sonra:

1. ✅ `variant_group_sku` field'ı eklenecek
2. ✅ Mevcut ürünlerde boş olacak
3. ✅ Yeni ürünlerde kullanılabilir
4. ✅ API response'larda `variant_group_products` otomatik gelecek

## 💡 Önemli Notlar

- **Ana ürün yok**: Tüm ürünler eşit seviyede
- **SKU takibi**: Her varyantın kendi SKU'su var
- **Stok yönetimi**: Her varyant kendi stokunu yönetir
- **İndeks**: `variant_group_sku` field'ı indexed, hızlı sorgulama

## 🔗 API Endpoints

### Product List
```
GET /api/products/
- variant_group_sku dahil
- variant_group_products dahil
```

### Product Detail
```
GET /api/products/{id}/
- variant_group_sku dahil
- variant_group_products detaylı
```

### Product Create/Update
```
POST/PATCH /api/products/{id}/
Body: {
  "variant_group_sku": "GROUP-SKU"
}
```

## ✨ Sonuç

Bu sistem ile:
- ✅ Karmaşık ilişkiler yok
- ✅ Her ürün bağımsız
- ✅ SKU bazlı otomatik gruplama
- ✅ Production-ready
- ✅ Kolay bakım

Artık varyantları SKU bazlı yönetebilirsin! 🎉
