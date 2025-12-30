# Aras Kargo Frontend - Backend Alan Eşleştirmesi

## Frontend Form Alanları → Backend Field Mapping

### 1. API Key / Kullanıcı Adı / Email
- **Frontend:** `api_key` 
- **Backend:** `IntegrationProvider.api_key` (şifreli)
- **Kullanım:** SetOrder için username (ikinci fotoğraftaki "Kullanıcı Adı")
- **Değer:** `samet@avrupamutfak.com`

### 2. API Secret / Şifre
- **Frontend:** `api_secret`
- **Backend:** `IntegrationProvider.api_secret` (şifreli)
- **Kullanım:** SetOrder için password (ikinci fotoğraftaki "Şifre")
- **Değer:** `mfG159753*`

### 3. API Endpoint
- **Frontend:** `api_endpoint`
- **Backend:** `IntegrationProvider.api_endpoint`
- **Not:** Production endpoint (test modunda kullanılmaz)

### 4. Test Endpoint
- **Frontend:** `test_endpoint`
- **Backend:** `IntegrationProvider.test_endpoint`
- **ZORUNLU:** Test modunda tam URL olmalı
- **Değer:** `https://customerservicestest.araskargo.com.tr/arascargoservice/arascargoservice.asmx`

### 5. Config JSON Field (Aras Kargo Ayarları)
Frontend'den `config` objesi içinde gönderilmeli:

```json
{
  "config": {
    "customer_code": "2528005751349",           // Müşteri Numarası
    "account_id": "2528005751349",              // Account ID (takip linki için)
    "customer_username": "Avrupamutfak1!",      // Müşteri Kullanıcı Adı
    "customer_password": "Avrupamutfak1!",      // Müşteri Şifre
    "branch": "Odin",                           // Şube
    "printer_type": "ZPL",                      // Yazıcı Tipi
    "setorder": {
      "username": "samet@avrupamutfak.com",     // SetOrder Kullanıcı Adı (opsiyonel)
      "password": "mfG159753*"                  // SetOrder Şifre (opsiyonel)
    }
  }
}
```

## Önemli Notlar

1. **SetOrder Credentials Öncelik Sırası:**
   - Önce `config.setorder.username` / `config.setorder.password` kullanılır
   - Yoksa `api_key` / `api_secret` kullanılır

2. **Frontend'den Gönderilmesi Gereken Format (PATCH/PUT):**
```json
{
  "api_key": "samet@avrupamutfak.com",
  "api_secret": "mfG159753*",
  "test_endpoint": "https://customerservicestest.araskargo.com.tr/arascargoservice/arascargoservice.asmx",
  "status": "test_mode",
  "config": {
    "customer_code": "2528005751349",
    "account_id": "2528005751349",
    "customer_username": "Avrupamutfak1!",
    "customer_password": "Avrupamutfak1!",
    "branch": "Odin",
    "printer_type": "ZPL"
  }
}
```

3. **Test Endpoint Formatı:**
   - ✅ Doğru: `https://customerservicestest.araskargo.com.tr/arascargoservice/arascargoservice.asmx`
   - ❌ Yanlış: `https://customerservicestest.araskargo.com.tr` (path eksik)

## Backend'de Kullanım

```python
# SetOrder credentials alınıyor:
credentials = {
    'user_name': config.setorder.username or api_key,  # samet@avrupamutfak.com
    'password': config.setorder.password or api_secret,  # mfG159753*
    'customer_code': config.customer_code,  # 2528005751349
    'customer_username': config.customer_username,  # Avrupamutfak1!
    'branch': config.branch,  # Odin
}
```

