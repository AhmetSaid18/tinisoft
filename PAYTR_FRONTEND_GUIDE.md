
# PayTR Direct API Frontend Entegrasyonu

Backend'den dönen response, PayTR'a yapılacak POST isteği için gerekli parametreleri içerir.
Frontend tarafında kullanıcıyı doğrudan URL'e yönlendirmek (**window.location.href = ...**) **YANLIŞTIR**.

Bunun yerine, backend'den gelen `data` objesindeki her bir parametreyi içeren gizli bir form (hidden form) oluşturulmalı ve bu form PayTR URL'ine POST edilmelidir.

## Backend Response Örneği

```json
{
  "success": true,
  "data": {
    "merchant_id": "XXXXXX",
    "user_ip": "85.105.100.100",
    "merchant_oid": "W123456789",
    "email": "musteri@example.com",
    "payment_amount": "10000",
    "paytr_token": "TOKEN_STRING...",
    "user_basket": "[...]",
    ...
  },
  "payment_url": "https://www.paytr.com/odeme",
  "method": "POST",
  "message": "PayTR ödeme formu için parametreler hazırlandı..."
}
```

## Frontend Yapması Gereken (JavaScript / React / Vue)
Backend'den bu response geldiğinde çalıştırılması gereken kod şuna benzer olmalıdır:

### Yöntem 1: Dinamik Form Oluşturma (Vanilla JS)

Bu fonksiyonu API response'u geldikten sonra çağırın:

```javascript
/**
 * PayTR ödeme formunu oluşturur ve submit eder.
 * @param {string} actionUrl - PayTR API URL (response.payment_url)
 * @param {object} formData - Backend'den gelen data objesi (response.data)
 */
function submitPayTRForm(actionUrl, formData) {
  // 1. Form elementini oluştur
  const form = document.createElement('form');
  form.method = 'POST';
  form.action = actionUrl;
  form.style.display = 'none'; // Kullanıcı görmesin

  // 2. Data içindeki her anahtar-değer çifti için input oluştur
  for (const key in formData) {
    if (formData.hasOwnProperty(key)) {
      const input = document.createElement('input');
      input.type = 'hidden';
      input.name = key;
      input.value = formData[key];
      form.appendChild(input);
    }
  }

  // 3. Formu sayfaya ekle ve submit et
  document.body.appendChild(form);
  form.submit();
  
  // İsteğe bağlı: Formu temizle (submit sonrası sayfa değişeceği için gerek kalmayabilir)
  // document.body.removeChild(form);
}

// KULLANIM:
// API call success olduğunda:
// submitPayTRForm(response.payment_url, response.data);
```

### Yöntem 2: React Component ile Render (Alternatif)

Eğer React kullanıyorsanız ve `dangerouslySetInnerHTML` veya ref kullanmak istemiyorsanız, bir form component'i render edip `useEffect` ile submit edebilirsiniz.

```jsx
import React, { useEffect, useRef } from 'react';

const PayTRRedirect = ({ paymentUrl, paymentData }) => {
  const formRef = useRef(null);

  useEffect(() => {
    if (formRef.current) {
      formRef.current.submit();
    }
  }, []);

  return (
    <form 
      ref={formRef} 
      action={paymentUrl} 
      method="POST" 
      style={{ display: 'none' }}
    >
      {Object.entries(paymentData).map(([key, value]) => (
        <input key={key} type="hidden" name={key} value={value} />
      ))}
    </form>
  );
};

export default PayTRRedirect;
```

## Özet
1. Backend `payment_url` ve `data` döner.
2. Frontend bu verilerle bir `<form method="POST" action="...">` oluşturur.
3. Form inputları `data` içindeki field'lardır.
4. Form otomatik olarak submit edilir (`form.submit()`).
5. Kullanıcı PayTR 3D Secure sayfasına yönlenir.
