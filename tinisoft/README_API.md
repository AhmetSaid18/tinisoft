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

## Postman Collection

Postman collection dosyası: `Tinisoft_API.postman_collection.json`

Import edip kullanabilirsin. Environment variables:
- `base_url`: `https://api.tinisoft.com.tr`
- `tenant_slug`: `my-store`
- `domain_id`: Domain ID (register sonrası)
- `owner_token`: Owner token (login sonrası)

