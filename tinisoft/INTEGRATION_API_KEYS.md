# Integration API Keys Yönetimi

## 🔐 Güvenli API Key Yönetim Sistemi

Tüm entegrasyonlar için (Kuveyt, Aras, Yurtiçi, Trendyol, Vakıf, vb.) merkezi ve şifreli API key yönetim sistemi.

---

## 🎯 Desteklenen Entegrasyonlar

### Ödeme Sağlayıcıları
- ✅ Kuveyt API
- ✅ İyzico
- ✅ PayTR
- ✅ Vakıf Bankası
- ✅ Garanti Bankası
- ✅ Akbank

### Kargo Sağlayıcıları
- ✅ Aras Kargo
- ✅ Yurtiçi Kargo
- ✅ MNG Kargo
- ✅ Sendex
- ✅ Trendyol Express

### E-Ticaret Platformları
- ✅ Trendyol Marketplace
- ✅ Hepsiburada
- ✅ N11
- ✅ GittiGidiyor

### Diğer Entegrasyonlar
- ✅ SMS Servisi
- ✅ Email Servisi
- ✅ Analytics

---

## 🔒 Güvenlik

- **Şifreleme**: Tüm API key'ler Fernet encryption ile şifrelenerek saklanır
- **Tenant Bazlı**: Her tenant'ın kendi entegrasyonları
- **Test Modu**: Test ve production modları ayrı endpoint'lerle yönetilir
- **Yetkilendirme**: Sadece tenant owner ve admin erişebilir

---

## 📝 Settings Konfigürasyonu

`settings.py` dosyasına encryption key ekleyin:

```python
# Integration API Keys Encryption Key
# Production'da mutlaka güçlü bir key kullanın!
# Key oluşturmak için: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
INTEGRATION_ENCRYPTION_KEY = env('INTEGRATION_ENCRYPTION_KEY', default=None)
```

**ÖNEMLİ**: Production'da mutlaka `INTEGRATION_ENCRYPTION_KEY` environment variable'ını ayarlayın!

---

## 🚀 API Kullanımı

### 1. Entegrasyon Oluşturma

**Endpoint**: `POST /api/integrations/`

**Örnek - Kuveyt API (Production)**:
```json
{
  "provider_type": "kuveyt",
  "name": "Kuveyt API - Production",
  "description": "Production ortamı için Kuveyt API entegrasyonu",
  "status": "active",
  "api_key": "your-production-api-key",
  "api_secret": "your-production-api-secret",
  "api_endpoint": "https://api.kuveyt.com/payment",
  "test_endpoint": "https://test-api.kuveyt.com/payment",
  "config": {
    "merchant_id": "12345",
    "return_url": "https://yoursite.com/payment/return",
    "cancel_url": "https://yoursite.com/payment/cancel"
  }
}
```

**Örnek - Kuveyt API (Test Modu)**:
```json
{
  "provider_type": "kuveyt",
  "name": "Kuveyt API - Test",
  "description": "Test ortamı için Kuveyt API entegrasyonu",
  "status": "test_mode",
  "api_key": "your-test-api-key",
  "api_secret": "your-test-api-secret",
  "api_endpoint": "https://api.kuveyt.com/payment",
  "test_endpoint": "https://test-api.kuveyt.com/payment",
  "config": {}
}
```

**Örnek - Aras Kargo**:
```json
{
  "provider_type": "aras",
  "name": "Aras Kargo Entegrasyonu",
  "description": "Aras Kargo API entegrasyonu",
  "status": "active",
  "api_key": "your-aras-api-key",
  "api_secret": "your-aras-api-secret",
  "api_endpoint": "https://api.araskargo.com.tr",
  "config": {
    "customer_code": "12345",
    "branch_code": "001"
  }
}
```

**Response**:
```json
{
  "success": true,
  "message": "Entegrasyon oluşturuldu.",
  "integration": {
    "id": "...",
    "provider_type": "kuveyt",
    "provider_type_display": "Kuveyt API",
    "name": "Kuveyt API - Production",
    "status": "active",
    "status_display": "Aktif",
    "api_endpoint": "https://api.kuveyt.com/payment",
    "test_endpoint": "https://test-api.kuveyt.com/payment",
    "config": {...},
    "created_at": "2024-01-10T10:00:00Z"
  }
}
```

**Not**: API key'ler response'da gösterilmez (güvenlik için).

---

### 2. Entegrasyon Listesi

**Endpoint**: `GET /api/integrations/`

**Query Parameters**:
- `provider_type`: Filtreleme (örn: `kuveyt`, `aras`)
- `status`: Durum filtresi (`active`, `inactive`, `test_mode`)
- `ordering`: Sıralama

**Örnek**:
```
GET /api/integrations/?provider_type=kuveyt&status=active
```

---

### 3. Entegrasyon Detayı

**Endpoint**: `GET /api/integrations/{integration_id}/`

---

### 4. Entegrasyon Güncelleme

**Endpoint**: `PATCH /api/integrations/{integration_id}/`

**Örnek - Test Moduna Geçiş**:
```json
{
  "status": "test_mode"
}
```

**Örnek - API Key Güncelleme**:
```json
{
  "api_key": "new-api-key",
  "api_secret": "new-api-secret"
}
```

---

### 5. Entegrasyon Test Etme

**Endpoint**: `POST /api/integrations/{integration_id}/test/`

Entegrasyonun çalışıp çalışmadığını test eder.

**Response**:
```json
{
  "success": true,
  "test_result": {
    "success": true,
    "message": "Kuveyt API bağlantısı test edildi.",
    "endpoint": "https://test-api.kuveyt.com/payment",
    "test_mode": true
  }
}
```

---

### 6. Provider Tipine Göre Aktif Entegrasyon

**Endpoint**: `GET /api/integrations/type/{provider_type}/`

Aktif veya test modundaki entegrasyonu getirir.

**Örnek**:
```
GET /api/integrations/type/kuveyt/
```

---

### 7. Entegrasyon Silme

**Endpoint**: `DELETE /api/integrations/{integration_id}/`

Soft delete yapılır (geri alınabilir).

---

## 💳 Ödeme İşlemlerinde Kullanım

Entegrasyon oluşturulduktan sonra, ödeme işlemlerinde otomatik olarak kullanılır:

**Örnek - Ödeme Oluşturma**:
```json
POST /api/payments/create/
{
  "order_id": "...",
  "provider": "kuveyt"
  // config göndermenize gerek yok, otomatik integration'dan alınır
}
```

Sistem otomatik olarak:
1. Tenant'ın aktif `kuveyt` entegrasyonunu bulur
2. API key'leri decrypt eder
3. Test modundaysa test endpoint kullanır
4. Ödeme işlemini gerçekleştirir

---

## 🔄 Test Modu

Test modu için:
1. Entegrasyon oluştururken `status: "test_mode"` kullanın
2. `test_endpoint` alanını doldurun
3. Test modunda sistem otomatik olarak `test_endpoint` kullanır

**Örnek**:
```json
{
  "provider_type": "kuveyt",
  "name": "Kuveyt API - Test",
  "status": "test_mode",
  "api_key": "test-api-key",
  "api_secret": "test-api-secret",
  "api_endpoint": "https://api.kuveyt.com/payment",
  "test_endpoint": "https://test-api.kuveyt.com/payment"
}
```

---

## 📋 Provider Type Listesi

Tüm provider type'lar:

- `kuveyt` - Kuveyt API
- `iyzico` - İyzico
- `paytr` - PayTR
- `vakif` - Vakıf Bankası
- `garanti` - Garanti Bankası
- `akbank` - Akbank
- `aras` - Aras Kargo
- `yurtici` - Yurtiçi Kargo
- `mng` - MNG Kargo
- `sendex` - Sendex
- `trendyol` - Trendyol Express
- `trendyol_marketplace` - Trendyol Marketplace
- `hepsiburada` - Hepsiburada
- `n11` - N11
- `gittigidiyor` - GittiGidiyor
- `sms` - SMS Servisi
- `email` - Email Servisi
- `analytics` - Analytics
- `other` - Diğer

---

## 🛡️ Güvenlik Notları

1. **Encryption Key**: Production'da mutlaka güçlü bir encryption key kullanın
2. **API Key'ler**: Response'larda API key'ler gösterilmez
3. **Yetkilendirme**: Sadece tenant owner ve admin erişebilir
4. **Soft Delete**: Silinen entegrasyonlar geri alınabilir
5. **Test Modu**: Test ve production modları ayrı yönetilir

---

## 📝 Migration

Model değişiklikleri için migration oluşturun:

```bash
python manage.py makemigrations
python manage.py migrate
```

---

## 🔧 Geliştirici Notları

### Yeni Provider Ekleme

1. `IntegrationProvider.ProviderType` enum'ına yeni tip ekleyin
2. İlgili provider service'i oluşturun (örn: `ArasCargoProvider`)
3. Test endpoint'i implement edin

### Encryption Key Oluşturma

```python
from cryptography.fernet import Fernet
key = Fernet.generate_key()
print(key.decode())  # Bu key'i settings'e ekleyin
```

---

## ❓ Sorular

Sorularınız için dokümantasyonu kontrol edin veya geliştirici ekibiyle iletişime geçin.

