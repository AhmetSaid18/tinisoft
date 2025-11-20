## Marketplace API

- **Servis:** `Tinisoft.Marketplace.API`
- **Varsayılan Host/Port:** `http://{env-host}:5005`
- **Base Path:** `/api/marketplace`
- **Sorumluluk:** Tenant bazlı pazar yeri (Trendyol, Hepsiburada, N11) entegrasyonları için ürün ve sipariş senkronizasyonu tetiklemek.

### Erişim Gereksinimleri
- `Authorization: Bearer <jwt>` — Kimlik doğrulama Tinisoft API Gateway üzerinden yapılır ve JWT Marketplace servisine forward edilir. Lokal çalıştırmada Auth middleware aktif değilse gateway olmadan da tetiklenebilir.
- `X-Tenant-Id: <tenant-guid>` — Finbuckle Multi-Tenant header stratejisi ile zorunlu. Tenant bilgisi olmadan integration bulunamaz ve istek 404 döner.

### Rate Limiti
`RateLimitingMiddleware` Redis üzerinden tenant + IP bazlı aşağıdaki limitleri uygular:
- 60 istek/dakika
- 1.000 istek/saat
- 10.000 istek/gün

Limit aşıldığında `429 Too Many Requests` ve `Retry-After: 60` header’ı döner. Frontend tekrar denemeden önce `retryAfter` alanını dikkate almalı.

### Sağlık Kontrolü
- `GET /health` — Health Checks paketi, DB bağlantısını (ApplicationDbContext) doğrular. 200 dönerse servis + DB sağlıklı demektir.

---

## Endpointler

### POST `/api/marketplace/sync/products`
Marketplace’e ürün push işlemini tek seferlik manuel tetikler. Handler `SyncProductsCommandHandler` içinde çalışır.

**Headers**
- `Authorization` (gateway üzerinden zorunlu)
- `X-Tenant-Id` (zorunlu)
- `Content-Type: application/json`

**Request Body (`SyncProductsCommand`)**

| Alan | Tip | Zorunlu | Açıklama |
| --- | --- | --- | --- |
| `marketplace` | string | ✔ | Desteklenen değerler: `Trendyol`, `Hepsiburada`, `N11`. Factory içinde `ToLower()` ile eşleştirilir, bu nedenle frontend küçük/büyük harf hassasiyetinden bağımsız güvenle kullanabilir. |
| `productIds` | Guid[] | ✖ | Belirli ürünleri göndermek için GUID listesi. `null` veya boş bırakılırsa tenant’ın tüm aktif ürünleri marketplace servisi tarafından senkronize edilir. |

**Örnek İstek**
```json
POST /api/marketplace/sync/products HTTP/1.1
Host: marketplace.api.internal:5005
Authorization: Bearer eyJhbGciOi...
X-Tenant-Id: 6f7f9c5d-4f7a-48a9-9b1a-a62f2f2c0c8e
Content-Type: application/json

{
  "marketplace": "Trendyol",
  "productIds": [
    "c2a1d4ac-8d7d-4b47-a57d-08dc5a7b1234",
    "c5df57f2-6f4d-4519-95ea-08dc5a7b5678"
  ]
}
```

**Başarılı Yanıt (`SyncProductsResponse`)**

| Alan | Tip | Açıklama |
| --- | --- | --- |
| `syncedCount` | int | Marketplace’e başarıyla gönderilen ürün sayısı. |
| `failedCount` | int | İletilemeyen ürün sayısı. |
| `errors` | string[] | Marketplace servisinden dönen hata mesajları (ürün bazlı). |

```json
HTTP/1.1 200 OK
{
  "syncedCount": 2,
  "failedCount": 0,
  "errors": []
}
```

**İş Kuralları & Validasyon**
- Handler tenant id’yi `IMultiTenantContextAccessor` üzerinden çeker ve `MarketplaceIntegration` tablosunda aktif kayıt arar. Yoksa `MarketplaceIntegrationNotFoundException` fırlatır.
- Integration bulunduğunda `ApiKey` boşsa `ApiKeyMissingException` ile 400 döner.
- `productIds` null ise servis tarafı tüm uygun ürünleri çeker; belirli bir liste gönderildiğinde concurrency açısından UI aynı anda birden fazla sync kuyruğa koymamalıdır.
- Sync sonucu integration kaydına `LastSyncAt` ve `LastSyncStatus` güncellenir.

### Hata Kodları

| HTTP | Kod | Senaryo | Body Örneği |
| --- | --- | --- | --- |
| 400 | `API_KEY_MISSING` | Integration var fakat `ApiKey` tanımlı değil. | `{"error":"Trendyol entegrasyonu için API anahtarı eksik","code":"API_KEY_MISSING","marketplace":"Trendyol"}` |
| 400 | `VALIDATION_ERROR` | FluentValidation veya komut validasyonu başarısız. | `{"error":"Doğrulama hatası oluştu.","code":"VALIDATION_ERROR","errors":{"marketplace":["Zorunlu"]}}` |
| 404 | `MARKETPLACE_INTEGRATION_NOT_FOUND` | Tenant için marketplace entegrasyonu aktif değil. | `{"error":"Trendyol entegrasyonu bulunamadı","code":"MARKETPLACE_INTEGRATION_NOT_FOUND","marketplace":"Trendyol"}` |
| 404 | `NOT_FOUND` | Handler içinde ek resource aramaları başarısız olursa (genel amaçlı). | `{"error":"Product not found","code":"NOT_FOUND","resource":"Product","key":"c2a1..."}` |
| 401 | `UNAUTHORIZED` | Gateway JWT doğrulaması başarısız veya header eksik. | `{"error":"Unauthorized","code":"UNAUTHORIZED"}` |
| 429 | — | Rate limit aşıldı. | `{"error":"Too many requests per minute","retryAfter":60}` |
| 500 | `INTERNAL_SERVER_ERROR` | Yakalanmayan tüm hatalar. | `{"error":"Bir hata oluştu. Lütfen daha sonra tekrar deneyin.","code":"INTERNAL_SERVER_ERROR"}` |

---

### Operasyonel Notlar
- Marketplace servisi `ApplicationDbContext` migration’larını development modunda otomatik çalıştırır; prod deployment’ta migration manuel tetiklenmelidir.
- Redis zorunludur; rate limiting middleware Redis bağlantısı yoksa dev ortamda devre dışı bırakılmalıdır.
- `TrendyolMarketplaceService`, `HepsiburadaMarketplaceService`, `N11MarketplaceService` şu an mock döner; gerçek entegrasyon sırasında aynı sözleşmeler korunmalıdır.

