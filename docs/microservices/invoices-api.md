# Invoices Microservice API

**Service:** `Tinisoft.Invoices.API`  
**Base Path:** `/api/invoices`  
**Auth:** Tenant admin/system service JWT. Tüm uçlar IMediator üzerinden `Tinisoft.Application.Invoices` katmanındaki komut/sorgulara gider.

---

## 1. Listeleme & Detay

### GET `/api/invoices`
- **Query (`GetInvoicesQuery`):**

| Param | Tip | Açıklama |
| --- | --- | --- |
| `page` | int | Varsayılan `1`. |
| `pageSize` | int | Varsayılan `20`. |
| `status` | string? | `Draft`, `Sent`, `Approved`, `Rejected`, `Cancelled`. |
| `invoiceType` | string? | `eFatura`, `EArsiv`. |
| `orderId` | GUID? | Sipariş filtresi. |
| `startDate` / `endDate` | DateTime? | Tarih filtresi. |
| `customerName`, `invoiceNumber` | string? | Serbest arama. |
| `sortBy` | string? | `InvoiceDate`, `InvoiceNumber`, `Total`, `Status`. |
| `sortOrder` | string? | `ASC` / `DESC` (varsayılan `DESC`). |

- **Response (`GetInvoicesResponse`):** `invoices[]` (`InvoiceListItemDto`), `totalCount`, `page`, `pageSize`, `totalPages`.  
`InvoiceListItemDto` alanları: `invoiceId`, `invoiceNumber`, `invoiceSerial`, `invoiceDate`, `invoiceType`, `status`, `statusMessage`, `orderId`, `orderNumber`, `customerName`, `customerEmail`, `total`, `currency`, `gibInvoiceId`, `gibInvoiceNumber`, `gibSentAt`, `gibApprovalStatus`, `isCancelled`, `cancelledAt`, `createdAt`.

### GET `/api/invoices/{id}`
- **Query:** `includePdf` (bool, varsayılan `false`).
- **Response (`GetInvoiceResponse`):** Detay alanları:
  - Temel: `invoiceId`, `invoiceNumber`, `invoiceSerial`, `invoiceDate`, `invoiceType`, `profileId`, `status`, `statusMessage`.
  - Sipariş: `orderId`, `orderNumber`.
  - Müşteri: `customerName`, `customerEmail`, `customerVKN`.
  - Tutarlar: `subtotal`, `taxAmount`, `discountAmount`, `shippingAmount`, `total`, `currency`.
  - GİB: `gibInvoiceId`, `gibInvoiceNumber`, `gibSentAt`, `gibApprovedAt`, `gibApprovalStatus`.
  - PDF: `pdfUrl`, `pdfGeneratedAt` (yalnız `includePdf=true` ise dolu).
  - Kalemler: `items[]` (`InvoiceItemResponse`: `invoiceItemId`, `productId`, `productVariantId`, `itemName`, `itemCode`, `quantity`, `unit`, `unitPrice`, `lineTotal`, `taxRatePercent`, `taxAmount`, `lineTotalWithTax`, `position`).
  - Metadata: `createdAt`, `updatedAt`.

---

## 2. Fatura Yaşam Döngüsü

### POST `/api/invoices`
- **Body (`CreateInvoiceCommand`):**

| Alan | Tip | Açıklama |
| --- | --- | --- |
| `orderId`* | GUID | Faturası çıkacak sipariş. |
| `invoiceType` | string? | `eFatura`/`EArsiv`; boşsa tenant ayarı. |
| `profileId` | string? | `TICARIFATURA`, `EARSIVFATURA`. |
| `invoiceDate` | DateTime? | Varsayılan bugün. |
| `autoSendToGIB` | bool | Varsayılan `true`. |

- **Response (`CreateInvoiceResponse`):** `invoiceId`, `invoiceNumber`, `invoiceSerial`, `status`, `gibInvoiceId`, `pdfUrl`, `message`.

### POST `/api/invoices/{id}/cancel`
- **Body (`CancelInvoiceCommand`):** `invoiceId` (controller set eder), `cancellationReason`*, `createCancellationInvoice` (varsayılan `true`).
- **Response:** `invoiceId`, `invoiceNumber`, `status`, `cancellationInvoiceNumber`, `message`.

### POST `/api/invoices/{id}/send-to-gib`
- **Body:** none; `SendInvoiceToGIBCommand` sadece `invoiceId`.
- **Response:** `invoiceId`, `invoiceNumber`, `success`, `gibInvoiceId`, `gibInvoiceNumber`, `errorMessage`, `message`.

### GET `/api/invoices/{id}/gib-status`
- **Response (`GetInvoiceStatusFromGIBResponse`):** `invoiceId`, `invoiceNumber`, `success`, `status` (`Onaylandı`, `Reddedildi`, `İşleniyor`, `Gönderildi`), `statusMessage`, `processedAt`, `gibInvoiceId`.

### GET `/api/invoices/inbox`
- **Query (`GetInboxInvoicesQuery`):** `startDate`, `endDate`, `senderVKN`.
- **Response:** `invoices[]` (`InboxInvoiceDto`: `invoiceId`, `invoiceNumber`, `invoiceDate`, `senderVKN`, `senderName`, `total`, `status`), `totalCount`.

---

## 3. Ayarlar

### GET `/api/invoices/settings`
- **Response (`GetInvoiceSettingsResponse`):** Tenant seviyesinde tüm alanlar:
  - E-Fatura bilgileri: `isEFaturaUser`, `VKN`, `TCKN`, `taxOffice`, `taxNumber`, `eFaturaAlias`.
  - Firma bilgileri, banka bilgileri, mali mühür meta verileri (`maliMuhurSerialNumber`, `hasMaliMuhur`, vb.).
  - Numara ayarları: `invoicePrefix`, `invoiceSerial`, `invoiceStartNumber`, `lastInvoiceNumber`.
  - Varsayılanlar: `defaultInvoiceType`, `defaultProfileId`, `paymentDueDays`.
  - Otomasyon: `autoCreateInvoiceOnOrderPaid`, `autoSendToGIB`.
  - Entegrasyon: `useTestEnvironment`, `isActive`.

### PUT `/api/invoices/settings`
- **Body (`UpdateInvoiceSettingsCommand`):** Aynı alanların opsiyonel versiyonları (nullable). Ayrıca banka/şirket bilgilerinin hepsi, mali mühür Base64 ve şifresi, invoice prefix/serial, otomasyon bayrakları.
- **Response (`UpdateInvoiceSettingsResponse`):** `tenantId`, `isEFaturaUser`, `VKN`, `message`.

---

## 4. Gelen Faturalar

### GET `/api/invoices/inbox`
- `GetInboxInvoicesQuery` yukarıda açıklandı; tenant’ın GİB inbox’ındaki faturaları listeler.

---

## Notlar
- GİB işlemleri uzun sürebileceği için frontend polling yapacaksa `GetInvoiceStatusFromGIB` uçunu kullanmalıdır.
- `CreateInvoiceCommand` `autoSendToGIB=false` seçilirse manuel göndermek için `send-to-gib` uçunu çağırmak gerekir.
- `includePdf=true` parametresi PDF üretir; sahte isteklerle aşırı yüklenmesini engellemek için UI debounce uygulamalıdır.

