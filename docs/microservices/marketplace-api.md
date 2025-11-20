# Marketplace Microservice API

**Service:** `Tinisoft.Marketplace.API`  
**Base Path:** `/api/marketplace`  
**Auth:** Tenant admin/service JWT. Marketplace sync işlemleri planlanan job/ayarlarla tetiklenir.

---

## 1. Ürün Senkronizasyonu

### POST `/api/marketplace/sync/products`
- **Body (`SyncProductsCommand`):**

| Alan | Tip | Açıklama |
| --- | --- | --- |
| `marketplace`* | string | Hedef pazar yeri (`Trendyol`, `Hepsiburada`, `N11`, vb.). |
| `productIds` | GUID[]? | Belirli ürünleri gönder; `null` veya boş ise tüm aktif ürünler senkronize edilir. |

- **Response (`SyncProductsResponse`):**

| Alan | Tip | Açıklama |
| --- | --- | --- |
| `syncedCount` | int | Başarılı gönderim sayısı. |
| `failedCount` | int | Hata veren ürün sayısı. |
| `errors[]` | string[] | Hata mesajları (ürün/variant bazlı). |

---

## Notlar
- Komut concurrency-safe olacak şekilde sıraya alınmalıdır; UI aynı anda birden fazla marketplace sync tetiklememeli.
- `marketplace` kodu handler içinde switch-case ile doğrulanır; UI sabit değerler kullanmalı (örn. `Trendyol` case-sensitive).

