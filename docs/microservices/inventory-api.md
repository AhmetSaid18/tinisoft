# Inventory Microservice API

**Service:** `Tinisoft.Inventory.API`  
**Base Path:** `/api/inventory`  
**Auth:** Tenant internal service token (Gateway policy). Müşteri-facing çağrılar storefront üzerinden yapılır.

---

## 1. Stok Takibi

### GET `/api/inventory/products/{productId}`
- **Query Parametreleri:**

| Param | Tip | Açıklama |
| --- | --- | --- |
| `variantId` | GUID? | Variant bazlı stok dönmek için opsiyonel. |

- **Response (`GetStockLevelResponse`):**

| Alan | Tip | Açıklama |
| --- | --- | --- |
| `productId` | GUID | Sorgulanan ürün. |
| `variantId` | GUID? | Variant varsa. |
| `quantity` | int? | Takip edilmiyorsa `null`. |
| `trackInventory` | bool | Ürün stok takibi açık mı. |
| `isInStock` | bool | `trackInventory` + `quantity>0`. |
| `isLowStock` | bool | Stok eşiği altı (handler içinde hesaplanır). |

### POST `/api/inventory/adjust`
- **Amaç:** Manuel stok ayarlaması (restock, return, sale vb.).
- **Body (`AdjustStockCommand`):**

| Alan | Tip | Açıklama |
| --- | --- | --- |
| `productId`* | GUID | Gerekli. |
| `variantId` | GUID? | Variant stok ucu. |
| `quantityChange`* | int | Pozitif/negatif delta. |
| `reason`* | string | `Restock`, `Sale`, `Return`, `Adjustment` vb. |
| `notes` | string? | Opsiyonel açıklama. |

- **Response (`AdjustStockResponse`):** `productId`, `variantId`, `oldQuantity`, `newQuantity`.

---

## Notlar
- Stok eşikleri domain handler'larında saklanır; UI `isLowStock` alanını kullanmalıdır.
- Variant içermeyen ürünler için `variantId` gönderilmez; false bir variant ID UI tarafından üretilmemelidir.

