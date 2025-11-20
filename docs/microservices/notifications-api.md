# Notifications Microservice API

**Service:** `Tinisoft.Notifications.API`  
**Base Path:** `/api/notifications`  
**Auth:** `[RequireRole("TenantAdmin","SystemAdmin")]` tüm uçlar için geçerli.  
**Amaç:** Email sağlayıcı ayarları, şablon yönetimi ve transactional email gönderimi.

---

## 1. Email Sağlayıcıları

### POST `/api/notifications/email-providers`
- **Body (`CreateEmailProviderCommand`):**

| Alan | Tip | Açıklama |
| --- | --- | --- |
| `providerName`* | string | Görünen ad (örn. `Tenant SMTP`). |
| `smtpHost`*, `smtpPort` | string/int | Varsayılan port `587`. |
| `enableSsl` | bool | Varsayılan `true`. |
| `smtpUsername`, `smtpPassword` | string | Kimlik bilgileri. |
| `fromEmail`, `fromName` | string | Gönderici. |
| `replyToEmail` | string? | Opsiyonel. |
| `settingsJson` | string? | Sağlayıcıya özel config. |
| `isDefault` | bool | Varsayılan `false`. |

- **Response (`CreateEmailProviderResponse`):** `emailProviderId`, `providerName`.

### PUT `/api/notifications/email-providers/{id}`
- Şu an controller'da PUT yok; ayar güncellemesi `Tinisoft.Application` katmanında planlanıyor. (UI bu uç gelene kadar provider sil/güncelle özelliğini göstermemeli.)

---

## 2. Email Şablonları

### POST `/api/notifications/email-templates`
- **Body (`CreateEmailTemplateCommand`):** `templateCode`, `templateName`, `subject`, `bodyHtml`, `bodyText`.
- **Response (`CreateEmailTemplateResponse`):** `emailTemplateId`, `templateCode`, `templateName`.

### GET `/api/notifications/email-templates`
- **Query (`GetEmailTemplatesQuery`):** `isActive` (bool?).
- **Response (`GetEmailTemplatesResponse`):** `templates[]` (`EmailTemplateDto`: `id`, `templateCode`, `templateName`, `subject`, `isActive`).

---

## 3. Email Gönderimi

### POST `/api/notifications/send-email`
- **Body (`SendEmailCommand`):**

| Alan | Tip | Açıklama |
| --- | --- | --- |
| `toEmail`* | string | Alıcı adresi. |
| `toName` | string? | — |
| `ccEmail`, `bccEmail` | string? | Opsiyonel. |
| `subject`* | string | Başlık (template ile override edilebilir). |
| `bodyHtml`* | string | HTML içerik. |
| `bodyText` | string? | Plain text fallback. |
| `emailTemplateId` | GUID? | Var olan template'ten doldurmak için. |
| `referenceId` | GUID? | İlgili kaynak (OrderId vb.). |
| `referenceType` | string? | `Order`, `Product`, `Customer`, … |

- **Response (`SendEmailResponse`):** `emailNotificationId`, `success`, `errorMessage`.
- Controller başarısız `success=false` olduğunda HTTP 400 döner; UI hata mesajını kullanıcıya göstermeli.

---

## Notlar
- Tüm uçlar tenant scoped çalışır; provider ve template kayıtları tenant bazında izole.
- Şablon `templateCode` değerleri frontend’te enum gibi tutulmalı (ör. `ORDER_SHIPPED`).

