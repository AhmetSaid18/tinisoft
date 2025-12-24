# Tinisoft API Documentation

Base URL: `https://api.tinisoft.com.tr`

## Authentication

### Owner (Mağaza Sahibi) Kayıt

**Endpoint:** `POST /api/auth/register/`

**Request Body:**
```json
{
    "email": "owner@example.com",
    "password": "password123",
    "first_name": "John",
    "last_name": "Doe",
    "phone": "+905551234567",
    "store_name": "My Store",
    "store_slug": "my-store",
    "custom_domain": "example.com"  // Opsiyonel
}
```

**Response:**
```json
{
    "success": true,
    "message": "Kayıt başarılı! Mağazanız oluşturuldu.",
    "user": {
        "id": "uuid",
        "email": "owner@example.com",
        "role": "owner",
        "role_display": "Owner"
    },
    "tenant": {
        "id": "uuid",
        "name": "My Store",
        "slug": "my-store",
        "subdomain": "my-store",
        "subdomain_url": "https://my-store.domains.tinisoft.com.tr",
        "custom_domain": "example.com",
        "custom_domain_url": "https://example.com",
        "status": "pending"
    },
    "verification_code": "abc123...",
    "verification_instructions": "DNS kaydı ekle..."
}
```

### Owner Giriş

**Endpoint:** `POST /api/auth/login/`

**Request Body:**
```json
{
    "email": "owner@example.com",
    "password": "password123"
}
```

### TenantUser (Müşteri) Kayıt

**Endpoint:** `POST /api/tenant/{tenant_slug}/users/register/`

**Request Body:**
```json
{
    "email": "customer@example.com",
    "password": "password123",
    "first_name": "Jane",
    "last_name": "Smith",
    "phone": "+905559876543"
}
```

### TenantUser Giriş

**Endpoint:** `POST /api/tenant/{tenant_slug}/users/login/`

**Request Body:**
```json
{
    "email": "customer@example.com",
    "password": "password123"
}
```

## Domain Management

### Domain Listesi

**Endpoint:** `GET /api/domains/`

**Headers:**
```
Authorization: Bearer {token}
```

**Response:**
```json
{
    "success": true,
    "domains": [
        {
            "id": "uuid",
            "domain_name": "example.com",
            "tenant_name": "My Store",
            "is_primary": true,
            "is_custom": true,
            "verification_status": "pending",
            "ssl_enabled": true
        }
    ]
}
```

### Domain Doğrulama

**Endpoint:** `POST /api/domains/{domain_id}/verify/`

**Headers:**
```
Authorization: Bearer {token}
```

**Response:**
```json
{
    "success": true,
    "message": "Domain doğrulaması başlatıldı.",
    "domain": {
        "id": "uuid",
        "domain_name": "example.com",
        "verification_status": "verifying",
        "verification_code": "abc123...",
        "verification_instructions": "DNS kaydı ekle..."
    }
}
```

### Domain Durumu

**Endpoint:** `GET /api/domains/{domain_id}/status/`

**Headers:**
```
Authorization: Bearer {token}
```

**Response:**
```json
{
    "success": true,
    "domain": {
        "id": "uuid",
        "domain_name": "example.com",
        "verification_status": "verified",
        "is_primary": true,
        "is_custom": true,
        "ssl_enabled": true,
        "verified_at": "2024-01-01T00:00:00Z"
    },
    "tenant": {
        "id": "uuid",
        "name": "My Store",
        "status": "active"
    }
}
```

## Domain Doğrulama Süreci

1. **Register** ile custom domain ekle
2. Response'dan `verification_code` al
3. DNS kaydı ekle:
   - **TXT Record:** `tinisoft-verify={verification_code}`
   - **VEYA CNAME:** `tinisoft-verify.example.com` → `verify.tinisoft.com.tr`
4. `POST /api/domains/{domain_id}/verify/` çağır
5. `GET /api/domains/{domain_id}/status/` ile durumu kontrol et
6. Domain doğrulandıktan sonra site yayınlanır

## Integration API Keys

### Entegrasyon Oluşturma

**Endpoint:** `POST /api/integrations/`

**Request Body (Kuveyt API Örneği):**
```json
{
  "provider_type": "kuveyt",
  "name": "Kuveyt API - Production",
  "description": "Production ortamı için",
  "status": "active",
  "api_key": "your-api-key",
  "api_secret": "your-api-secret",
  "api_endpoint": "https://api.kuveyt.com/payment",
  "test_endpoint": "https://test-api.kuveyt.com/payment",
  "config": {
    "return_url": "https://yoursite.com/payment/return",
    "cancel_url": "https://yoursite.com/payment/cancel"
  }
}
```

**Test Modu:**
```json
{
  "provider_type": "kuveyt",
  "name": "Kuveyt API - Test",
  "status": "test_mode",
  "api_key": "test-api-key",
  "api_secret": "test-api-secret",
  "test_endpoint": "https://test-api.kuveyt.com/payment"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Entegrasyon oluşturuldu.",
  "integration": {
    "id": "uuid",
    "provider_type": "kuveyt",
    "provider_type_display": "Kuveyt API",
    "name": "Kuveyt API - Production",
    "status": "active",
    "status_display": "Aktif",
    "api_endpoint": "https://api.kuveyt.com/payment",
    "test_endpoint": "https://test-api.kuveyt.com/payment"
  }
}
```

### Entegrasyon Listesi

**Endpoint:** `GET /api/integrations/`

**Query Parameters:**
- `provider_type`: Filtreleme (kuveyt, aras, vb.)
- `status`: Durum filtresi (active, inactive, test_mode)

### Entegrasyon Güncelleme

**Endpoint:** `PATCH /api/integrations/{integration_id}/`

**Test Modundan Canlı Moda Geçiş:**
```json
{
  "status": "active",
  "api_key": "production-api-key",
  "api_secret": "production-api-secret"
}
```

### Entegrasyon Test Etme

**Endpoint:** `POST /api/integrations/{integration_id}/test/`

## Ödeme İşlemleri

### Ödeme Oluşturma (Kuveyt API)

**Endpoint:** `POST /api/payments/create/`

**Request Body:**
```json
{
  "order_id": "order-uuid",
  "provider": "kuveyt",
  "customer_info": {
    "email": "customer@example.com",
    "name": "Ahmet Yılmaz",
    "phone": "+905551234567"
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Ödeme oluşturuldu.",
  "payment": {
    "id": "uuid",
    "payment_number": "PAY-TENANT-...",
    "status": "pending"
  },
  "payment_url": "https://api.kuveyt.com/payment/redirect/...",
  "transaction_id": "TRX123456789"
}
```

**Not:** Integration oluşturulduktan sonra config göndermenize gerek yok, sistem otomatik olarak integration'dan alır.

### Ödeme Doğrulama (Callback)

**Endpoint:** `POST /api/payments/verify/`

**Request Body:**
```json
{
  "transaction_id": "TRX123456789",
  "provider": "kuveyt"
}
```

## Sepet ve Sipariş

### Sepete Kupon Uygulama

**Endpoint:** `POST /api/cart/coupon/`

**Request Body:**
```json
{
  "coupon_code": "KUPON123"
}
```

**Kuponu Kaldırma:**
```
DELETE /api/cart/coupon/
```

### Public Kupon Listesi

**Endpoint:** `GET /api/public/coupons/`

Müşterilerin görebileceği aktif kuponları listeler.

### Müşteri Sipariş Takip

**Endpoint:** `GET /api/orders/track/{order_number}/`

Sipariş numarası ile sipariş durumunu takip eder (public endpoint).

**Response:**
```json
{
  "success": true,
  "order": {
    "order_number": "ORD-TENANT-12345678-ABCD1234",
    "status": "shipped",
    "status_display": "Kargoya Verildi",
    "payment_status": "paid",
    "tracking_number": "ARAS123456789",
    "shipped_at": "2024-01-15T10:30:00Z",
    "total": "150.00",
    "currency": "TRY"
  }
}
```

### Müşteri Kendi Siparişlerini Görüntüleme

**Endpoint:** `GET /api/orders/`

Müşteriler sadece kendi siparişlerini görür. Tenant owner/admin tüm siparişleri görür.

## Postman Collection

Postman collection dosyası: `Tinisoft_API.postman_collection.json`

Import edip kullanabilirsin. Environment variables:
- `base_url`: `https://api.tinisoft.com.tr`
- `tenant_slug`: `my-store`
- `domain_id`: Domain ID (register sonrası)
- `owner_token`: Owner token (login sonrası)

## Detaylı Dokümantasyon

- **[Özellikler Özeti](FEATURES_SUMMARY.md)** - Tüm özellikler ve kullanım senaryoları
- **[Integration API Keys](INTEGRATION_API_KEYS.md)** - Entegrasyon API key yönetimi detayları
- **[Ödeme Akışı](PAYMENT_FLOW.md)** - Tam ödeme ve sipariş takip akışı

