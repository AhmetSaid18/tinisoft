# Aras Kargo Takip Linki Entegrasyonu

Bu dokümantasyon, Aras Kargo kargo takip web sayfası entegrasyonu hakkında detaylı bilgiler içerir.

## Özet

Aras Kargo, müşterilerinin kendi web sitelerine veya uygulamalarına entegre edebilecekleri üç farklı takip linki formatı sunar.

## Takip Linki Formatları

### 1. Kargo Takip Numarası ile Takip (13 haneli)

```
http://kargotakip.araskargo.com.tr/mainpage.aspx?code=3513773163316
```

**Parametreler:**
- `code`: Aras Kargo'nun gönderi kaydı oluştururken ürettiği 13 haneli kargo takip kodu
- **Özellikler:**
  - Benzersizdir
  - Özel fonksiyon ile üretilir

### 2. Sipariş Numarası ile Takip (M.Ö.K - Müşteri Özel Kodu)

```
http://kargotakip.araskargo.com.tr/mainpage.aspx?accountid=CBAD417894B73048BBC058C09771CDB8&sifre=nd1234&alici_kod=6140307
```

**Parametreler:**
- `accountid`: Aras Kargo tarafından sağlanan sabit hesap kodu (müşterinin Aras Kargo sistemindeki hesap kodu)
- `sifre`: Güvenlik şifresi - kayıt olurken müşteri veya Aras Kargo tarafından oluşturulan sabit değer
- `alici_kod`: Müşteri özel kodu (M.Ö.K) - kargo takibi için kullanılan referans numarası

**Önemli Notlar:**
- `accountid` ve `sifre` sabit değerlerdir (her istekte aynı)
- `alici_kod` dinamiktir (her kargo için değişir)
- `alici_kod`, Aras Kargo'nun gönderi kaydı oluştururken kaydettiği referans numarasıdır

### 3. Kargo Barkod Kodu ile Takip (20 haneli)

```
http://kargotakip.araskargo.com.tr/yurticigonbil.aspx?Cargo_Code=0805513773163332313
```

**Parametreler:**
- `Cargo_Code`: Aras Kargo'nun gönderi kaydı oluştururken ürettiği 20 haneli barkod kodu
- **Özellikler:**
  - Benzersizdir
  - Özel fonksiyon ile üretilir

## Güvenlik Önerileri

⚠️ **ÖNEMLİ:**

1. **ACCOUNTID ve ŞİFRE gizli tutulmalıdır**
   - Bu parametreler kendi kullanıcılarınızla paylaşılmamalıdır
   - Paylaşılması durumunda, `alici_kod` değiştirilerek aynı firmanın başka gönderilerine ulaşılabilir
   - Bu bir güvenlik açığı oluşturur ve Aras Kargo bu durumda sorumluluk kabul etmez

2. **Link Saklama Yöntemleri**
   - Parametreleri gizlemek için `<iframe>` yöntemi kullanılabilir
   - "Sanal Adres" yöntemi de kullanılabilir

## Üyelik ve Kayıt

1. Aras Kargo'nun Kurumsal web sayfasına giriş yapın
2. "Tanımlamalar" linkine tıklayın
3. "Entegrasyonlar" sekmesine gidin
4. "Kargo Takip Web Sayfası Üyeliği" linkine tıklayın
5. Açılan formu doldurarak Size Özel Kargo Takip Linki üretin

## Sistem Gereksinimleri

- Kargo kaydı oluştururken, Aras Kargo Şubesi kargo takip numarası ile ilgili alana giriş yapmalıdır
- Kargo takibi yapmaya başlamadan önce Aras Kargo Şubenizi bu konuda uyarınız

## Kod Örneği

### Python/Django Kullanımı

```python
from apps.services.aras_cargo_service import ArasCargoService

# Sipariş numarası ile takip linki
tracking_url = ArasCargoService.get_tracking_url(
    tenant=tenant,
    tracking_reference='ORDER123',  # Müşteri Özel Kodu
    tracking_type='order_number'
)

# Kargo takip numarası ile (13 haneli)
tracking_url = ArasCargoService.get_tracking_url(
    tenant=tenant,
    tracking_reference='3513773163316',
    tracking_type='tracking_number'
)

# Barkod kodu ile (20 haneli)
tracking_url = ArasCargoService.get_tracking_url(
    tenant=tenant,
    tracking_reference='0805513773163332313',
    tracking_type='barcode'
)
```

### iframe Entegrasyonu (Önerilen)

```html
<!-- Güvenli iframe kullanımı -->
<iframe 
    src="http://kargotakip.araskargo.com.tr/mainpage.aspx?accountid=XXX&sifre=YYY&alici_kod=ZZZ"
    width="100%" 
    height="600px"
    frameborder="0">
</iframe>
```

## Mevcut Implementasyon

Servisimizde `ArasCargoService.get_tracking_url()` metodu bu üç formatı da destekler:

- ✅ Tracking Number (13 haneli)
- ✅ Order Number / M.Ö.K (accountid, sifre, alici_kod)
- ✅ Barcode Code (20 haneli)

Tüm linkler otomatik olarak oluşturulur ve URL encoding uygulanır.

## Kaynak

- Aras Kargo Kurumsal Web Sayfası
- Kargo Takip Web Sayfası Üyeliği Dokümantasyonu

