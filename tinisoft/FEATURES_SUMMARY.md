# Özellikler Özeti ve Kullanım Kılavuzu

**Son Güncelleme:** 2024 - Integration API Keys, Payment Provider Sistemi, Kupon Yönetimi

## ✅ Mevcut Özellikler

### 1. **Favorilere Ekleme (Wishlist)** ✅
- **Endpoint**: `/api/wishlists/`
- Müşteriler ürünleri favorilerine ekleyebilir
- Birden fazla wishlist oluşturulabilir

### 2. **Sepet (Cart)** ✅
- **Endpoint**: `/api/cart/`
- Sepete ürün ekleme, çıkarma, güncelleme
- Guest checkout desteği

### 3. **Ödeme (Payment)** ✅
- **Endpoint**: `/api/payments/`
- Genel ödeme sistemi mevcut
- **YENİ**: Kuveyt API entegrasyonu eklendi (aşağıda detaylar)

### 4. **Kupon Sistemi** ✅
- **Endpoint**: `/api/coupons/`
- Kupon oluşturma, doğrulama
- **YENİ**: Sepete kupon uygulama eklendi
- **YENİ**: Public kupon listesi eklendi

### 5. **Sipariş Yönetimi** ✅
- **Endpoint**: `/api/orders/`
- Sipariş oluşturma
- **YENİ**: Müşteri sipariş takip endpoint'i eklendi

### 6. **Reviews** ✅
- **Endpoint**: `/api/products/{product_id}/reviews/`
- Ürün yorumları ve puanlama

### 7. **Kargo Yöntemleri** ✅
- **Endpoint**: `/api/shipping/methods/`
- Kargo yöntemi tanımlama (Aras Kargo örneği mevcut)
- Not: API entegrasyonu henüz yok, sadece model var

---

## 🆕 Yeni Eklenen Özellikler

### 1. **Sepete Kupon Uygulama** 🆕

**Endpoint**: `POST /api/cart/coupon/`

**Kullanım**:
```json
POST /api/cart/coupon/
{
  "coupon_code": "KUPON123"
}
```

**Kuponu Kaldırma**:
```json
DELETE /api/cart/coupon/
```

**Response**:
```json
{
  "success": true,
  "message": "Kupon sepete uygulandı.",
  "cart": {
    "id": "...",
    "subtotal": "100.00",
    "discount_amount": "10.00",
    "total": "90.00",
    "coupon": {
      "code": "KUPON123",
      "name": "Yüzde 10 İndirim"
    }
  }
}
```

---

### 2. **Public Kupon Listesi** 🆕

**Endpoint**: `GET /api/public/coupons/`

Müşterilerin görebileceği aktif kuponları listeler.

**Response**:
```json
{
  "success": true,
  "coupons": [
    {
      "code": "KUPON123",
      "name": "Yüzde 10 İndirim",
      "description": "Tüm ürünlerde geçerli",
      "discount_type": "percentage",
      "discount_value": "10.00",
      "minimum_order_amount": "50.00",
      "valid_until": "2024-12-31T23:59:59Z"
    }
  ]
}
```

---

### 3. **Müşteri Sipariş Takip** 🆕

**Endpoint**: `GET /api/orders/track/{order_number}/`

Müşteriler sipariş numarası ile sipariş durumunu takip edebilir.

**Kullanım**:
```
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

### 4. **Kuveyt API Entegrasyonu** 🆕

#### 4.1. Ödeme Oluşturma

**Endpoint**: `POST /api/payments/create/`

**Kullanım**:
```json
POST /api/payments/create/
{
  "order_id": "uuid-here",
  "provider": "kuwait",
  "provider_config": {
    "api_key": "your-api-key",
    "api_secret": "your-api-secret",
    "endpoint": "https://api.kuveyt.com/payment",
    "return_url": "https://yoursite.com/payment/return",
    "cancel_url": "https://yoursite.com/payment/cancel"
  },
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
    "status": "pending",
    "amount": "150.00"
  },
  "payment_url": "https://api.kuveyt.com/payment/redirect/...",
  "transaction_id": "TRX123456789"
}
```

#### 4.2. Ödeme Doğrulama (Callback)

**Endpoint**: `POST /api/payments/verify/`

Kuveyt API'den callback geldiğinde ödemeyi doğrular.

**Kullanım**:
```json
POST /api/payments/verify/
{
  "transaction_id": "TRX123456789",
  "provider": "kuwait"
}
```

**Response**:
```json
{
  "success": true,
  "message": "Ödeme doğrulandı ve tamamlandı.",
  "payment": {
    "id": "...",
    "status": "completed",
    "paid_at": "2024-01-10T15:30:00Z"
  }
}
```

#### 4.3. Tenant Ayarları

Tenant'ın `metadata` alanında Kuveyt API bilgilerini saklayabilirsiniz:

```python
tenant.metadata = {
    "payment_providers": {
        "kuwait": {
            "api_key": "your-api-key",
            "api_secret": "your-api-secret",
            "endpoint": "https://api.kuveyt.com/payment",
            "return_url": "https://yoursite.com/payment/return",
            "cancel_url": "https://yoursite.com/payment/cancel"
        }
    }
}
tenant.save()
```

Bu şekilde her ödeme isteğinde config göndermenize gerek kalmaz.

---

## 🆕 Son Eklenen Özellikler (2024)

### 1. **Integration API Keys Sistemi** 🆕
- Tüm entegrasyonlar için merkezi API key yönetimi
- Şifreli saklama (Fernet encryption)
- Test modu desteği
- Desteklenen entegrasyonlar:
  - Ödeme: Kuveyt, İyzico, PayTR, Vakıf, Garanti, Akbank
  - Kargo: Aras, Yurtiçi, MNG, Sendex, Trendyol Express
  - Marketplace: Trendyol, Hepsiburada, N11, GittiGidiyor
  - Diğer: SMS, Email, Analytics

### 2. **Payment Provider Sistemi** 🆕
- Genişletilebilir ödeme sağlayıcı sistemi
- Kuveyt API entegrasyonu
- Otomatik integration'dan config alma
- Test ve production modları

### 3. **Sepete Kupon Uygulama** 🆕
- `POST /api/cart/coupon/` - Kuponu sepete uygula
- `DELETE /api/cart/coupon/` - Kuponu sepetten kaldır
- Otomatik indirim hesaplama

### 4. **Public Kupon Listesi** 🆕
- `GET /api/public/coupons/` - Müşterilerin görebileceği aktif kuponlar
- Tarih ve kullanım limiti kontrolü

### 5. **Müşteri Sipariş Takip** 🆕
- `GET /api/orders/track/{order_number}/` - Public sipariş takip
- Müşteriler kendi siparişlerini görüntüleyebilir (`GET /api/orders/`)

## ❌ Henüz Eklenmeyen Özellikler

### 1. **Ürün Karşılaştırma**
- Ürünlerin karşılaştırılması için özel bir özellik henüz yok
- Not: `compare_at_price` alanı mevcut ama karşılaştırma listesi özelliği yok

### 2. **Kargo API Entegrasyonları**
- Kargo yöntemi modeli var ama API entegrasyonları henüz yok
- Integration sistemi hazır, sadece provider implementasyonu gerekiyor

---

## 📝 Kullanım Senaryosu: Müşteri Ödeme Akışı

1. **Ürün Sepete Ekleme**:
   ```
   POST /api/cart/add/
   {
     "product_id": "...",
     "quantity": 2
   }
   ```

2. **Kupon Uygulama**:
   ```
   POST /api/cart/coupon/
   {
     "coupon_code": "KUPON123"
   }
   ```

3. **Sipariş Oluşturma**:
   ```
   POST /api/orders/
   {
     "cart_id": "...",
     "customer_email": "customer@example.com",
     "customer_first_name": "Ahmet",
     "customer_last_name": "Yılmaz",
     "customer_phone": "+905551234567",
     "shipping_address": {...}
   }
   ```

4. **Ödeme Oluşturma (Kuveyt API)**:
   ```
   POST /api/payments/create/
   {
     "order_id": "...",
     "provider": "kuwait",
     "customer_info": {...}
   }
   ```

5. **Müşteri Ödeme Sayfasına Yönlendirilir**:
   - Response'daki `payment_url`'e yönlendirilir
   - Kuveyt API'de ödeme yapar

6. **Callback (Ödeme Doğrulama)**:
   ```
   POST /api/payments/verify/
   {
     "transaction_id": "...",
     "provider": "kuwait"
   }
   ```

7. **Sipariş Takibi**:
   ```
   GET /api/orders/track/ORD-TENANT-12345678-ABCD1234/
   ```

---

## 🔧 Geliştirici Notları

### Payment Provider Sistemi

Yeni payment provider eklemek için:

1. `tinisoft/apps/services/payment_providers.py` dosyasına yeni provider class'ı ekleyin
2. `PaymentProviderFactory.PROVIDERS` dict'ine ekleyin
3. Provider'ın `create_payment()` ve `verify_payment()` metodlarını implement edin

Örnek:
```python
class IyzicoPaymentProvider(PaymentProviderBase):
    def create_payment(self, order, amount, customer_info):
        # Iyzico API entegrasyonu
        pass
    
    def verify_payment(self, transaction_id):
        # Iyzico doğrulama
        pass

# Factory'ye ekle
PaymentProviderFactory.PROVIDERS['iyzico'] = IyzicoPaymentProvider
```

---

## 🔐 Güvenlik ve İzolasyon

### Tenant İzolasyonu
- ✅ **Schema-based izolasyon**: Her tenant'ın ayrı database schema'sı
- ✅ **Model seviyesinde**: Tüm tenant-specific modellerde `tenant` ForeignKey
- ✅ **View seviyesinde**: Her view'da `get_tenant_from_request()` kontrolü
- ✅ **Müşteri izolasyonu**: Her müşteri sadece kendi tenant'ına ait
- ✅ **Sipariş izolasyonu**: Her sipariş tenant'a bağlı
- ✅ **Ödeme izolasyonu**: Her tenant'ın kendi API key'leri

### API Key Güvenliği
- ✅ **Şifreli saklama**: Fernet encryption ile
- ✅ **Response'da gizleme**: API key'ler response'larda gösterilmez
- ✅ **Tenant bazlı**: Her tenant sadece kendi entegrasyonlarına erişebilir
- ✅ **Test modu**: Test ve production modları ayrı yönetilir

## 📞 Destek

Sorularınız için lütfen dokümantasyonu kontrol edin veya geliştirici ekibiyle iletişime geçin.

## 📚 İlgili Dokümantasyon

- **[API Dokümantasyonu](../README_API.md)** - Tüm API endpoint'leri
- **[Integration API Keys](INTEGRATION_API_KEYS.md)** - Entegrasyon yönetimi detayları
- **[Ödeme Akışı](PAYMENT_FLOW.md)** - Tam ödeme ve sipariş akışı
- **[Database Mimari](DATABASE_ARCHITECTURE.md)** - Multi-tenant database yapısı

