# Aras Kargo Integration - Gerekli Alanlar

## Frontend Form Alanları

Integration panelinde Aras Kargo için şu alanlar gerekli:

### 1. Temel Bilgiler
- **Aktif** (Checkbox) → `status: "active"` veya `"inactive"`
- **Kullanıcı Adı** → `api_key` (şifreli saklanır)
- **Şifre** → `api_secret` (şifreli saklanır)

### 2. Müşteri Bilgileri
- **Müşteri Numarası** → `config.customer_code`
- **Müşteri Kullanıcı Adı** → `config.customer_username` (opsiyonel)
- **Müşteri Şifre** → `config.customer_password` (opsiyonel)

### 3. SetOrder Bilgileri (Gönderi Oluşturma)
- **SetOrder Kullanıcı Adı** → `config.setorder.username` (email'den gelen)
- **SetOrder Şifre** → `config.setorder.password` (email'den gelen)

### 4. Takip Linki Bilgileri
- **Account ID** → `config.account_id` (Aras panelinden alınan)
- **Tracking Password** → `config.tracking_password` (opsiyonel, yeni format gerekmiyor)

### 5. Ek Ayarlar
- **Şube** → `config.branch` (örn: "Odin")
- **Yazıcı Tipi** → `config.printer_type` (örn: "ZPL", "PDF")

### 6. Endpoint'ler
- **API Endpoint** → `api_endpoint` (Canlı ortam)
- **Test Endpoint** → `test_endpoint` (Test ortamı)

## API Request Örneği

```json
{
  "provider_type": "aras",
  "name": "Aras Kargo Entegrasyonu",
  "description": "Aras Kargo API entegrasyonu",
  "status": "active",
  "api_key": "samet@avrupamutfak.com",
  "api_secret": "mfG159753*",
  "api_endpoint": "http://customerservices.araskargo.com.tr/ArasCargoCustomerIntegrationService/ArasCargoIntegrationService.svc",
  "test_endpoint": "http://test-customerservices.araskargo.com.tr/ArasCargoCustomerIntegrationService/ArasCargoIntegrationService.svc",
  "config": {
    "customer_code": "2528005751349",
    "customer_username": "Avrupamutfak1!",
    "customer_password": "Avrupamutfak1!",
    "account_id": "D6BF9768BD782049A02991658F276B6B",
    "tracking_password": "",
    "branch": "Odin",
    "printer_type": "ZPL",
    "setorder": {
      "username": "Onl*B50OpMYe",
      "password": "V5KNEuaZ%glI",
      "customer_code": "2528005751349"
    }
  }
}
```

## Alan Açıklamaları

- **Kullanıcı Adı/Şifre**: Query servisleri (GetQueryDS) için
- **Müşteri Kullanıcı Adı/Şifre**: Bazı API çağrılarında gerekebilir
- **SetOrder Bilgileri**: Gönderi oluşturma (SetOrder API) için ayrı credentials
- **Şube**: Kargo şubesi bilgisi
- **Yazıcı Tipi**: Etiket yazdırma için (ZPL, PDF, vb.)

