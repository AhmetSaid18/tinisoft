# Orders Microservice API

**Service:** `Tinisoft.Orders.API`  
**Base Path:** `/api/orders`  
**Auth:** Tenant admin/service JWT (gateway policy). Public storefront çağrıları bu servis üzerinden değil `Customers API` üzerinden yapılır.

---

## 1. Sipariş Oluşturma

### POST `/api/orders`
- **Amaç:** Admin paneli veya diğer servisler (örn. checkout) tarafından sipariş kaydı oluşturur.
- **Body (`CreateOrderCommand`):**

| Alan | Tip | Açıklama |
| --- | --- | --- |
| `customerEmail`* | string | Müşteri e-postası. |
| `customerPhone` | string? | Opsiyonel iletişim. |
| `customerFirstName`, `customerLastName` | string? | — |
| `shippingAddressLine1/2` | string? | Gönderim adresi. |
| `shippingCity` | string? | — |
| `shippingState` | string? | — |
| `shippingPostalCode` | string? | — |
| `shippingCountry` | string? | ISO kodu. |
| `items[]`* | OrderItemDto[] | Ürün satırları. |
| `subtotal`, `tax`, `shipping`, `discount`, `total` | decimal | Toplamlar. |
| `shippingMethod` | string? | Kargo firması/metodu. |

`OrderItemDto` alanları: `productId`, `productVariantId`, `quantity`, `unitPrice`.

- **Response (`CreateOrderResponse`):** `orderId`, `orderNumber`, `total`.

---

## 2. Sipariş Detayı

### GET `/api/orders/{id}`
- **Path Param:** `id` (GUID).
- **Response (`GetOrderResponse`):**
  - `id`, `orderNumber`, `status`
  - Müşteri: `customerEmail`, `customerPhone`, `customerFirstName`, `customerLastName`
  - Finans: `totals` (`subtotal`, `tax`, `shipping`, `discount`, `total`), `paymentStatus`, `paymentProvider`, `paidAt`
  - Kargo: `shippingMethod`, `trackingNumber`
  - Zaman: `createdAt`
  - `items[]` (`OrderItemResponse`: `id`, `productId`, `productVariantId`, `title`, `quantity`, `unitPrice`, `totalPrice`)

---

## 3. Durum Güncelleme

### PUT `/api/orders/{id}/status`
- **Body (`UpdateOrderStatusCommand`):**

| Alan | Tip | Açıklama |
| --- | --- | --- |
| `orderId` | GUID | Controller path’ten set eder. |
| `status`* | string | `Pending`, `Paid`, `Processing`, `Shipped`, `Delivered`, `Cancelled`. |
| `trackingNumber` | string? | Yeni takip numarası. |

- **Response (`UpdateOrderStatusResponse`):** `orderId`, `status`.

---

## Notlar
- Servis içindeki tüm komutlar IMediator üstünden domain katmanına aktarılır; context header’larında tenant bilgisi gerekir.
- `CreateOrderCommand` shipping adresini opsiyonel tutar; fulfillment sadece dijital siparişler için adres olmadan da çalışır.

