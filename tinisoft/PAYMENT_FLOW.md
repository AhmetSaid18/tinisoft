# Ödeme Akışı ve Sipariş Takibi - Kullanım Kılavuzu

## ✅ Tam Akış Özeti

### 1. Tenant Kuveyt API Bağlama

**Adım 1: Test Modunda Entegrasyon Oluştur**
```json
POST /api/integrations/
{
  "provider_type": "kuveyt",
  "name": "Kuveyt API - Test",
  "description": "Test ortamı için",
  "status": "test_mode",
  "api_key": "test-api-key",
  "api_secret": "test-api-secret",
  "api_endpoint": "https://api.kuveyt.com/payment",
  "test_endpoint": "https://test-api.kuveyt.com/payment",
  "config": {
    "return_url": "https://yoursite.com/payment/return",
    "cancel_url": "https://yoursite.com/payment/cancel"
  }
}
```

**Adım 2: Test Et**
```json
POST /api/integrations/{integration_id}/test/
```

**Adım 3: Canlı Moda Geçiş**
```json
PATCH /api/integrations/{integration_id}/
{
  "status": "active",
  "api_key": "production-api-key",
  "api_secret": "production-api-secret"
}
```

---

### 2. Müşteri Alışveriş ve Ödeme Akışı

#### 2.1. Ürün Sepete Ekleme
```json
POST /api/cart/add/
{
  "product_id": "uuid-here",
  "quantity": 2
}
```

#### 2.2. Kupon Uygulama (Opsiyonel)
```json
POST /api/cart/coupon/
{
  "coupon_code": "KUPON123"
}
```

#### 2.3. Sepeti Görüntüleme
```json
GET /api/cart/
```

#### 2.4. Sipariş Oluşturma
```json
POST /api/orders/
{
  "cart_id": "uuid-here",
  "customer_email": "customer@example.com",
  "customer_first_name": "Ahmet",
  "customer_last_name": "Yılmaz",
  "customer_phone": "+905551234567",
  "shipping_address": {
    "address_line1": "Test Mahallesi",
    "address_line2": "Test Sokak No:1",
    "city": "Istanbul",
    "postal_code": "34000",
    "country": "TR"
  },
  "shipping_method_id": "uuid-here"
}
```

**Response**:
```json
{
  "success": true,
  "message": "Sipariş oluşturuldu.",
  "order": {
    "id": "...",
    "order_number": "ORD-TENANT-12345678-ABCD1234",
    "status": "pending",
    "payment_status": "pending",
    "total": "150.00",
    "currency": "TRY"
  }
}
```

#### 2.5. Ödeme Yapma (Kuveyt API)
```json
POST /api/payments/create/
{
  "order_id": "order-uuid-here",
  "provider": "kuveyt",
  "customer_info": {
    "email": "customer@example.com",
    "name": "Ahmet Yılmaz",
    "phone": "+905551234567"
  }
}
```

**Response**:
```json
{
  "success": true,
  "message": "Ödeme oluşturuldu.",
  "payment": {
    "id": "...",
    "payment_number": "PAY-TENANT-...",
    "status": "pending"
  },
  "payment_url": "https://api.kuveyt.com/payment/redirect/...",
  "transaction_id": "TRX123456789"
}
```

**Müşteri `payment_url`'e yönlendirilir ve Kuveyt API'de ödeme yapar.**

#### 2.6. Ödeme Doğrulama (Callback)
Kuveyt API'den callback geldiğinde:
```json
POST /api/payments/verify/
{
  "transaction_id": "TRX123456789",
  "provider": "kuveyt"
}
```

**Başarılı Response**:
```json
{
  "success": true,
  "message": "Ödeme doğrulandı ve tamamlandı.",
  "payment": {
    "status": "completed",
    "paid_at": "2024-01-10T15:30:00Z"
  }
}
```

**Sipariş otomatik olarak `confirmed` durumuna geçer ve `payment_status` `paid` olur.**

---

### 3. Sipariş Takibi

#### 3.1. Müşteri Kendi Siparişlerini Görüntüleme
```json
GET /api/orders/
```

**Müşteri sadece kendi siparişlerini görür.**

**Response**:
```json
{
  "success": true,
  "orders": [
    {
      "id": "...",
      "order_number": "ORD-TENANT-12345678-ABCD1234",
      "status": "confirmed",
      "status_display": "Onaylandı",
      "payment_status": "paid",
      "payment_status_display": "Ödendi",
      "total": "150.00",
      "currency": "TRY",
      "created_at": "2024-01-10T14:20:00Z",
      "item_count": 2
    }
  ]
}
```

#### 3.2. Müşteri Sipariş Detayı
```json
GET /api/orders/{order_id}/
```

#### 3.3. Sipariş Numarası ile Takip (Public)
```json
GET /api/orders/track/ORD-TENANT-12345678-ABCD1234/
```

**Response**:
```json
{
  "success": true,
  "order": {
    "order_number": "ORD-TENANT-12345678-ABCD1234",
    "status": "shipped",
    "status_display": "Kargoya Verildi",
    "payment_status": "paid",
    "payment_status_display": "Ödendi",
    "tracking_number": "ARAS123456789",
    "shipped_at": "2024-01-15T10:30:00Z",
    "delivered_at": null,
    "created_at": "2024-01-10T14:20:00Z",
    "total": "150.00",
    "currency": "TRY"
  }
}
```

---

### 4. Tenant Sipariş Yönetimi

#### 4.1. Tüm Siparişleri Görüntüleme
```json
GET /api/orders/
```

**Tenant owner/admin tüm siparişleri görür.**

**Query Parameters**:
- `status`: Filtreleme (pending, confirmed, shipped, vb.)
- `payment_status`: Ödeme durumu filtresi
- `customer_email`: Müşteri email filtresi
- `order_number`: Sipariş numarası filtresi

**Örnek**:
```
GET /api/orders/?status=confirmed&payment_status=paid
```

#### 4.2. Sipariş Detayı
```json
GET /api/orders/{order_id}/
```

#### 4.3. Sipariş Durumu Güncelleme
```json
PATCH /api/orders/{order_id}/
{
  "status": "shipped",
  "tracking_number": "ARAS123456789"
}
```

**Durumlar**:
- `pending` - Beklemede
- `confirmed` - Onaylandı
- `processing` - Hazırlanıyor
- `shipped` - Kargoya Verildi
- `delivered` - Teslim Edildi
- `cancelled` - İptal Edildi
- `refunded` - İade Edildi

#### 4.4. Ödeme Listesi
```json
GET /api/payments/
```

**Query Parameters**:
- `order_id`: Sipariş ID filtresi
- `status`: Ödeme durumu filtresi

---

## 🔄 Tam Akış Senaryosu

### Senaryo: Müşteri Alışveriş Yapıyor

1. **Müşteri siteye girer** → Tenant'ın subdomain'i üzerinden
2. **Ürünleri görüntüler** → `GET /api/public/products/`
3. **Sepete ürün ekler** → `POST /api/cart/add/`
4. **Kupon uygular** (opsiyonel) → `POST /api/cart/coupon/`
5. **Sepeti görüntüler** → `GET /api/cart/`
6. **Sipariş oluşturur** → `POST /api/orders/`
7. **Ödeme yapar** → `POST /api/payments/create/` → Kuveyt API'ye yönlendirilir
8. **Kuveyt API'de ödeme yapar** → Callback gelir
9. **Ödeme doğrulanır** → `POST /api/payments/verify/`
10. **Siparişi takip eder** → `GET /api/orders/` veya `GET /api/orders/track/{order_number}/`

### Senaryo: Tenant Sipariş Yönetimi

1. **Tenant admin paneline girer**
2. **Tüm siparişleri görüntüler** → `GET /api/orders/`
3. **Sipariş detayını görüntüler** → `GET /api/orders/{order_id}/`
4. **Siparişi onaylar** → `PATCH /api/orders/{order_id}/` → `status: "confirmed"`
5. **Kargoya verir** → `PATCH /api/orders/{order_id}/` → `status: "shipped"`, `tracking_number: "ARAS123456789"`
6. **Teslim edildi olarak işaretler** → `PATCH /api/orders/{order_id}/` → `status: "delivered"`

---

## ✅ Özet - Tüm Özellikler Çalışıyor

✅ **Tenant Kuveyt API bağlayabilir** → `POST /api/integrations/`  
✅ **Test modundan canlı moda geçebilir** → `PATCH /api/integrations/{id}/`  
✅ **Müşteriler siteden ödeme yapabilir** → `POST /api/payments/create/`  
✅ **Müşteriler siparişlerini takip edebilir** → `GET /api/orders/`  
✅ **Tenant tüm siparişleri görebilir** → `GET /api/orders/`  
✅ **Tenant sipariş durumunu güncelleyebilir** → `PATCH /api/orders/{id}/`  
✅ **Sipariş numarası ile public takip** → `GET /api/orders/track/{order_number}/`

---

## 🔐 Güvenlik

- Müşteriler sadece kendi siparişlerini görebilir
- Tenant owner/admin tüm siparişleri görebilir
- API key'ler şifreli saklanır
- Test ve production modları ayrı yönetilir

---

## 📝 Notlar

- Ödeme başarılı olduğunda sipariş otomatik olarak `confirmed` durumuna geçer
- Test modunda `test_endpoint` kullanılır
- Canlı modda `api_endpoint` kullanılır
- Integration aktif değilse ödeme oluşturulamaz

