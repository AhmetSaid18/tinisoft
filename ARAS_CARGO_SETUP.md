# Aras Kargo Entegrasyonu Kurulum Rehberi

Bu dokümantasyon, Aras Kargo entegrasyonunun sisteminize nasıl kurulacağını açıklar.

## Bilgiler

Aşağıdaki bilgiler Aras Kargo tarafından sağlanmıştır:

- **Firma Adı**: AVRUPA PROFESYONEL MUTFAK DAY.TÜK.ÜRÜNLERİ GIDA İÇ VE DIŞ TİC.LTD,ŞTİ.
- **Müşteri Kodu**: `2528005751349`
- **Kullanıcı Adı**: `mTn^NB7J0M0N`
- **Şifre**: `Wd4vDCL&a1$N`
- **Account ID**: `D6BF9768BD782049A02991658F276B6B` (Takip linki için)

## Kurulum

### 1. Management Command ile Kurulum

```bash
python manage.py setup_aras_cargo \
  --tenant-slug <tenant-slug> \
  --username "mTn^NB7J0M0N" \
  --password "Wd4vDCL&a1$N" \
  --customer-code "2528005751349" \
  --account-id "D6BF9768BD782049A02991658F276B6B" \
  --tracking-password "Wd4vDCL&a1$N" \
  --status active
```

**Örnek:**
```bash
python manage.py setup_aras_cargo \
  --tenant-slug avrupamutfak \
  --username "mTn^NB7J0M0N" \
  --password "Wd4vDCL&a1$N" \
  --customer-code "2528005751349" \
  --account-id "D6BF9768BD782049A02991658F276B6B" \
  --tracking-password "Wd4vDCL&a1$N" \
  --status active
```

### 2. API ile Kurulum

POST `/api/integrations/` endpoint'ini kullanarak entegrasyonu oluşturabilirsiniz:

```json
{
  "provider_type": "aras",
  "name": "Aras Kargo Entegrasyonu",
  "description": "Aras Kargo API entegrasyonu",
  "status": "active",
  "api_key": "mTn^NB7J0M0N",
  "api_secret": "Wd4vDCL&a1$N",
  "config": {
    "customer_code": "2528005751349",
    "account_id": "D6BF9768BD782049A02991658F276B6B",
    "tracking_password": "Wd4vDCL&a1$N"
  }
}
```

## Takip Linki Formatları

Aras Kargo üç farklı takip linki formatı destekler:

### 1. Kargo Takip Numarası ile (13 haneli)
```
http://kargotakip.araskargo.com.tr/mainpage.aspx?code=3513773163316
```

### 2. Sipariş Numarası ile (M.Ö.K - Müşteri Özel Kodu)
```
http://kargotakip.araskargo.com.tr/mainpage.aspx?accountid=D6BF9768BD782049A02991658F276B6B&sifre=Wd4vDCL&a1$N&alici_kod=6140307
```

### 3. Kargo Barkod Kodu ile (20 haneli)
```
http://kargotakip.araskargo.com.tr/yurticigonbil.aspx?Cargo_Code=0805513773163332313
```

## Servis Kullanımı

### Gönderi Oluşturma

```python
from apps.services.aras_cargo_service import ArasCargoService
from apps.models import Order

# Sipariş ve adres bilgileri ile gönderi oluştur
result = ArasCargoService.create_shipment(
    tenant=tenant,
    order=order,
    shipping_address={
        'first_name': 'Ahmet',
        'last_name': 'Yılmaz',
        'phone': '05321234567',
        'address_line_1': 'Örnek Mah. Örnek Sok. No:1',
        'city': 'İstanbul',
        'postal_code': '34000',
        'country': 'TR',
    }
)

if result['success']:
    print(f"Takip Numarası: {result['tracking_number']}")
    print(f"Takip Linki: {result['tracking_url']}")
```

### Gönderi Takibi

```python
result = ArasCargoService.track_shipment(
    tenant=tenant,
    tracking_number='3513773163316'
)

if result['success']:
    print(f"Durum: {result['status']}")
    print(f"Takip Linki: {result['tracking_url']}")
```

### Takip Linki Oluşturma

```python
# Sipariş numarası ile takip linki
tracking_url = ArasCargoService.get_tracking_url(
    tenant=tenant,
    tracking_reference='ORDER123',
    tracking_type='order_number'
)

# Kargo takip numarası ile takip linki (13 haneli)
tracking_url = ArasCargoService.get_tracking_url(
    tenant=tenant,
    tracking_reference='3513773163316',
    tracking_type='tracking_number'
)

# Barkod kodu ile takip linki (20 haneli)
tracking_url = ArasCargoService.get_tracking_url(
    tenant=tenant,
    tracking_reference='0805513773163332313',
    tracking_type='barcode'
)
```

## API Endpoints

- `POST /api/orders/{order_id}/aras/create-shipment/` - Gönderi oluştur
- `GET /api/aras/track/{tracking_number}/` - Gönderi takip et
- `GET /api/aras/label/{tracking_number}/` - Kargo etiketi yazdır
- `POST /api/aras/cancel/{tracking_number}/` - Gönderi iptal et

## Güvenlik Notları

⚠️ **ÖNEMLİ**: 
- `accountid` ve `sifre` (tracking_password) parametreleri güvenlik açısından kendi kullanıcılarınızla paylaşılmamalıdır.
- Paylaşılması durumunda `alici_kod` parametresi değiştirilerek aynı firmanın başka gönderilerine ulaşılabilir.
- Takip linklerini gizlemek için `<iframe>` veya "Sanal Adres" yöntemleri kullanılabilir.

## Test

Entegrasyonu test etmek için:

```bash
# Integration test endpoint'ini kullan
POST /api/integrations/{integration_id}/test/
```

## Destek

Aras Kargo dokümantasyonu için: `Aras Kargo-Müşteri Bilgi Sorgulama Servisleri.pdf`

