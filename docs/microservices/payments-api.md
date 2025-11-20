# Payments Microservice API

**Service:** `Tinisoft.Payments.API`  
**Base Path:** `/api/payments`  
**Auth:** Tenant backoffice/gateway token. PayTR callback ucu public fakat IP whitelisting beklenir.

---

## 1. Ödeme Alma

### POST `/api/payments/process`
- **Body (`ProcessPaymentCommand`):**

| Alan | Tip | Açıklama |
| --- | --- | --- |
| `orderId`* | GUID | Ödeme alınacak sipariş. |
| `paymentProvider` | string | Varsayılan `PayTR`; `Stripe`, `Iyzico` vb. için genişler. |
| `amount`* | decimal | Tahsil edilecek tutar. |
| `currency` | string | Varsayılan `TRY`. |
| `providerSpecificData` | Dictionary<string,string>? | Örn. kart token, installment bilgisi. |

- **Response (`ProcessPaymentResponse`):**
  - `success` (bool)
  - `paymentToken` (PayTR iframe token gibi)
  - `paymentReference`
  - `errorMessage`
  - `redirectUrl` (3DS veya hosted payment sayfası için)

UI `success=false` durumda `errorMessage` göstermeli.

---

## 2. Ödeme Doğrulama

### POST `/api/payments/verify`
- **Body (`VerifyPaymentCommand`):**

| Alan | Tip | Açıklama |
| --- | --- | --- |
| `orderId`* | GUID | İlgili sipariş. |
| `paymentReference`* | string | Sağlayıcı transaction numarası. |
| `hash`* | string | Sağlayıcıdan gelen imza. |
| `callbackData`* | Dictionary<string,string> | Ham callback payload’u (PayTR `POST` formu). |

- **Response (`VerifyPaymentResponse`):** `isValid`, `isPaid`, `errorMessage`.

---

## 3. PayTR Callback

### POST `/api/payments/callback/paytr`
- **Body:** PayTR’ın gönderdiği `application/x-www-form-urlencoded` alanı; controller’da `Dictionary<string,string>` olarak alınır.
- **Davranış:** Şu an iskelet halde; hash doğrulaması ve `merchant_oid` → `OrderId` eşlemesi yapılmalı. UI bu ucu doğrudan kullanmaz fakat webhooks için endpoint hazırdır.

---

## Notlar
- PayTR doğrulamasında `hash` değeri `PayTRService` içerisindeki shared secret ile karşılaştırılır; UI asla hash üretmez.
- Diğer ödeme sağlayıcıları eklendiğinde `paymentProvider` alanı switch-case ile yönlendirilir; UI sabit string kullanmalı (case-sensitive).

