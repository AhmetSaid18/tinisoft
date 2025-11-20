# Shipping Microservice API

**Service:** `Tinisoft.Shipping.API`  
**Base Path:** `/api/shipping`  
**Auth:** `[RequireRole("TenantAdmin","SystemAdmin")]` tüm uçlar.  
**Amaç:** Kargo sağlayıcı yönetimi, ücret hesaplama, gönderi oluşturma.

---

## 1. Kargo Sağlayıcıları

### GET `/api/shipping/providers`
- **Query (`GetShippingProvidersQuery`):** `isActive` (bool?).
- **Response (`GetShippingProvidersResponse`):** `providers[]` (`ShippingProviderDto`: `id`, `providerCode`, `providerName`, `isActive`, `isDefault`, `priority`, `useTestMode`, `hasApiKey`).

### POST `/api/shipping/providers`
- **Body (`CreateShippingProviderCommand`):**

| Alan | Tip | Açıklama |
| --- | --- | --- |
| `providerCode`* | string | Örn. `YURTICI`, `ARAS`. |
| `providerName`* | string | Gösterilen ad. |
| `apiKey`, `apiSecret` | string? | Sağlayıcı entegrasyonu için. |
| `apiUrl`, `testApiUrl` | string? | Endpoint adresleri. |
| `useTestMode` | bool | Varsayılan `false`. |
| `settingsJson` | string? | Sağlayıcıya özel JSON. |
| `isDefault` | bool | Varsayılan `false`. |
| `priority` | int | Varsayılan `0`. |

- **Response (`CreateShippingProviderResponse`):** `shippingProviderId`, `providerCode`, `providerName`.

### PUT `/api/shipping/providers/{id}`
- **Body (`UpdateShippingProviderCommand`):** Tüm alanlar opsiyonel ve partial update olarak çalışır: `providerName`, `apiKey`, `apiSecret`, `apiUrl`, `testApiUrl`, `useTestMode`, `settingsJson`, `isDefault`, `priority`, `isActive`.
- **Response (`UpdateShippingProviderResponse`):** `shippingProviderId`, `providerCode`, `providerName`.

---

## 2. Kargo Hesaplama & Gönderi

### POST `/api/shipping/calculate-cost`
- **Body (`CalculateShippingCostCommand`):**

| Alan | Tip | Açıklama |
| --- | --- | --- |
| `shippingProviderId` | GUID? | Belirli sağlayıcıyı zorla. |
| `providerCode` | string? | Alternatif seçim. |
| `fromCity`* | string | Çıkış. |
| `toCity`* | string | Varış. |
| `weight`* | decimal | KG. |
| `width`, `height`, `depth` | decimal? | Opsiyonel ölçüler. |

- **Response (`CalculateShippingCostResponse`):** `shippingCost`, `currency`, `providerCode`, `providerName`, `success`, `errorMessage`.

### POST `/api/shipping/shipments`
- **Body (`CreateShipmentCommand`):**
  - Sipariş: `orderId`, `shippingProviderId`
  - Alıcı: `recipientName`, `recipientPhone`, `addressLine1`, `addressLine2`, `city`, `state`, `postalCode`, `country`
  - Paket: `weight`, `width`, `height`, `depth`, `packageCount`
- **Response (`CreateShipmentResponse`):** `shipmentId`, `trackingNumber`, `labelUrl`, `shippingCost`, `success`, `errorMessage`.
- Controller başarı durumunda `201` döner, aksi halde `400`.

---

## Notlar
- Sağlayıcı API anahtarları loglanmaz; UI `hasApiKey` alanını kullanarak “konfigürasyon eksik” uyarısı gösterebilir.
- `CalculateShippingCostCommand` içinde hem `shippingProviderId` hem `providerCode` gönderilirse handler ID’yi önceliklendirir.

