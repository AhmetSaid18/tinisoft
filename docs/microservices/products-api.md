# Products Microservice API

**Service:** `Tinisoft.Products.API`  
**Base Path:** `/api`  
**Auth:** Tüm `/api/products` ve `/api/tax` uçları tenant access token/JWT ister. `StorefrontController` üzerindeki `[Public]` ile işaretli uçlar (müşteri-facing) herhangi bir auth header'ı beklemez ancak rate-limit/tenant context middleware'leri uygulanır.  
**Gateway:** İstekler varsayılan olarak `Tinisoft.API.Gateway` üzerinden yönlendirilir; doğrudan servis hit etmek için container portunu kullanabilirsiniz.

---

## 1. Yönetim Uçları – `ProductsController`

Kaynak: `src/Tinisoft.Products.API/Controllers/ProductsController.cs`

### GET `/api/products`
- **Amaç:** Tenant ürünlerini sayfalı olarak listeler.
- **Query Parametreleri**

| Alan | Tip | Açıklama / Varsayılan |
| --- | --- | --- |
| `page` | int | 1 tabanlı sayfa, varsayılan `1`. |
| `pageSize` | int | 1-100 arasında; varsayılan `20`. |
| `search` | string | Başlık/SKU'da arama. |
| `categoryId` | GUID | Kategori filtresi. |
| `isActive` | bool | Yayında/Yayında değil ürünler. |
| `sortBy` | string | `title`, `price`, `createdAt`. |
| `sortOrder` | string | `asc` veya `desc`. |

- **Response (`GetProductsResponse`)**

| Alan | Tip | Açıklama |
| --- | --- | --- |
| `items` | ProductListItemDto[] | Ürün kartları (aşağıda). |
| `totalCount` | int | Filtreli toplam kayıt. |
| `page` | int | İstenen sayfa. |
| `pageSize` | int | Kullanılan pageSize. |
| `totalPages` | int | `ceil(totalCount/pageSize)`. |

`ProductListItemDto` alanları: `id`, `title`, `slug`, `sku`, `price`, `compareAtPrice`, `inventoryQuantity`, `isActive`, `featuredImageUrl`, `createdAt`.

### GET `/api/products/{id}`
- **Amaç:** Tek ürünü tüm detaylarıyla getirir.
- **Path Param:** `id` (GUID).
- **Response (`GetProductResponse`)** – tüm alanlar:
  - Kimlik: `id`, `slug`, `sku`, `barcode`, `gtin`
  - İçerik: `title`, `description`, `shortDescription`
  - Fiyat/Stok: `price`, `compareAtPrice`, `costPerItem`, `currency`, `status`, `trackInventory`, `inventoryQuantity`, `allowBackorder`
  - Lojistik: `weight`, `weightUnit`, `length`, `width`, `height`, `requiresShipping`, `isDigital`
  - Vergi: `isTaxable`, `taxCode`, `chargeTaxes`, `taxCategory`
  - SEO/Meta: `metaTitle`, `metaDescription`, `metaKeywords`, `vendor`, `productType`, `publishedScope`, `templateSuffix`, `isGiftCard`, `inventoryManagement`, `fulfillmentService`, `countryOfOrigin`, `hsCode`
  - Satış kısıtları: `minQuantity`, `maxQuantity`, `incrementQuantity`, `shippingClass`, `barcodeFormat`, `unitPrice`, `unitPriceUnit`, `defaultInventoryLocationId`, `isActive`, `publishedAt`
  - Koleksiyonlar: `images[]`, `categories[]`, `variants[]`, `options[]`, `metafields[]`, `tags[]`, `collections[]`, `salesChannels[]`
  - Media/custom: `videoUrl`, `videoThumbnailUrl`, `customFields`
  - Zaman damgaları: `createdAt`, `updatedAt`.
  - Embedded DTO alanları:  
    - `ImageDto`: `id`, `originalUrl`, `thumbnailUrl`, `smallUrl`, `mediumUrl`, `largeUrl`, `altText`, `position`, `isFeatured`.  
    - `VariantDto`: `id`, `title`, `sku`, `price`, `inventoryQuantity`.  
    - `OptionDto`: `id`, `name`, `values[]`, `position`.  
    - `MetafieldDto`: `id`, `namespace`, `key`, `value`, `type`, `description`.  
    - `CategoryDto`: `id`, `name`, `slug`.

### POST `/api/products`
- **Amaç:** Yeni ürün oluşturur.
- **Body (`CreateProductCommand`)** – tüm alanlar; belirtilmemiş alanlar varsayılanı kullanır.

| Kategori | Alan | Tip | Varsayılan / Açıklama |
| --- | --- | --- | --- |
| Kimlik & içerik | `title`* | string | Ürün adı. |
|  | `description` | string? | Zengin açıklama. |
|  | `shortDescription` | string? | Liste kartı açıklaması. |
|  | `slug`* | string | URL slug. |
|  | `sku` | string? | Stok kodu. |
|  | `barcode`/`gtin` | string? | Barkod/GTIN. |
| Fiyatlama | `price`* | decimal | Vitrin satış fiyatı. |
|  | `compareAtPrice` | decimal? | İndirim öncesi fiyat. |
|  | `costPerItem`* | decimal | Maliyet. |
|  | `currency` | string | Varsayılan `TRY`. |
|  | `purchaseCurrency` | string? | Giriş para birimi. |
|  | `purchasePrice` | decimal? | Giriş fiyatı. |
|  | `autoConvertSalePrice` | bool | `true`. |
| Durum | `status` | string | `Draft/Active/Archived`, varsayılan `Draft`. |
|  | `isActive` | bool | `true`. |
| Envanter | `trackInventory` | bool | Varsayılan `false`. |
|  | `inventoryQuantity` | int? | Toplam stok. |
|  | `allowBackorder` | bool | Varsayılan `false`. |
|  | `inventoryPolicy` | string | `Deny`. |
| Fiziksel | `weight`/`length`/`width`/`height` | decimal? | Opsiyonel ölçüler. |
|  | `weightUnit` | string? | Varsayılan `kg`. |
| Kargo | `requiresShipping` | bool | `true`. |
|  | `isDigital` | bool | `false`. |
|  | `shippingWeight` | decimal? | Gönderi ağırlığı. |
| Vergi | `isTaxable` | bool | `true`. |
|  | `taxCode` | string? | E-fatura kodu. |
| SEO | `metaTitle`/`metaDescription`/`metaKeywords` | string? | React Helmet metadata. |
| Open Graph | `ogTitle`/`ogDescription`/`ogImage`/`ogType` | string? | Varsayılan `ogType = product`. |
| Twitter Card | `twitterCard` | string? | Varsayılan `summary_large_image`. |
|  | `twitterTitle`/`twitterDescription`/`twitterImage` | string? | — |
| Canonical | `canonicalUrl` | string? | — |
| Vendor/Type | `vendor`/`productType` | string? | — |
| Yayınlama | `publishedScope` | string | Varsayılan `web`. |
|  | `templateSuffix` | string? | Liquid template adı. |
| Gift Card | `isGiftCard` | bool | `false`. |
| Envanter yönetimi | `inventoryManagement` | string? | Örn. `Shopify`. |
|  | `fulfillmentService` | string? | — |
| Uluslararası | `countryOfOrigin` | string? | ISO ülke. |
|  | `hsCode` | string? | Gümrük kodu. |
| Satış kuralları | `minQuantity`/`maxQuantity`/`incrementQuantity` | int? | — |
| Kanallar | `salesChannels[]` | string[] | Örn. `["storefront","marketplace"]`. |
| Medya | `videoUrl`/`videoThumbnailUrl` | string? | — |
| Custom | `customFields` | Dictionary<string,object>? | Serbest alanlar. |
| Depo | `defaultInventoryLocationId` | GUID? | Varsayılan depo. |
| Barkod | `barcodeFormat` | string? | Örn. `EAN13`. |
| Birim fiyat | `unitPrice`/`unitPriceUnit` | decimal?/string? | — |
| Vergi ayrıntı | `chargeTaxes` | bool | `true`. |
|  | `taxCategory` | string? | — |
| Shipping | `shippingClass` | string? | — |
| İlişkiler | `images[]` | ImageInputDto[] | Base64 veya URL (aşağıda). |
|  | `options[]` | ProductOptionDto[] | Variant seçenekleri. |
|  | `metafields[]` | MetafieldDto[] | Custom namespace/key. |
|  | `categoryIds[]` | GUID[] | Ürün kategorileri. |
|  | `tags[]` | string[] | — |
|  | `collections[]` | string[] | — |
| Depo bazlı stok | `warehouseInventories[]` | WarehouseInventoryDto[] | Her depo için stok. |

`ImageInputDto`: `base64Data`, `url`, `altText`, `position`, `isFeatured`.  
`ProductOptionDto`: `name`, `values[]`, `position`.  
`MetafieldDto`: `namespace`, `key`, `value`, `type`, `description`.  
`WarehouseInventoryDto`: `warehouseId`, `quantity`, `minStockLevel`, `maxStockLevel`, `cost`, `location`.

- **Response (`CreateProductResponse`):** `productId`, `title`.

### PUT `/api/products/{id}`
- **Amaç:** Ürünün seçili alanlarını günceller.
- **Path Param:** `id` → body'deki `productId` overwrite edilir.
- **Body (`UpdateProductCommand`):** Tüm alanlar opsiyoneldir; boş bırakılan değerler değişmez.

| Alan | Tip | Not |
| --- | --- | --- |
| `productId` | GUID | Controller tarafından set edilir. |
| `title`, `description`, `slug`, `sku` | string? | — |
| `price`, `compareAtPrice`, `costPerItem` | decimal? | — |
| `purchaseCurrency`, `purchasePrice`, `autoConvertSalePrice` | string?/decimal?/bool? | — |
| `trackInventory`, `inventoryQuantity`, `isActive` | bool?/int? | — |
| SEO alanları | string? | `meta*`, `og*`, `twitter*`, `canonicalUrl`. |
| Görsel | `featuredImageUrl` | string? | — |
| Diğer görseller | `imageUrls` | string[]? | Basit URL listesi. |

- **Response (`UpdateProductResponse`):** `productId`, `title`.

### DELETE `/api/products/{id}`
- **Amaç:** Ürünü siler/yumuşak silme.
- **Response:** `204 No Content`.

---

## 2. Storefront (Public) Uçları – `StorefrontController`

Kaynak: `src/Tinisoft.Products.API/Controllers/StorefrontController.cs`

### GET `/api/storefront/products`
- **Auth:** Public.
- **Query Parametreleri:** `page`, `pageSize`, `search`, `categoryId`, `sortBy`, `sortOrder`, `preferredCurrency`.
- **Response (`GetStorefrontProductsResponse`):**
  - `items[]` → `StorefrontProductDto`: `id`, `title`, `slug`, `shortDescription`, `sku`, `price` (tenant kuruna göre), `compareAtPrice`, `currency`, `inventoryQuantity`, `isInStock`, `featuredImageUrl`, `categories[]`, `createdAt`.
  - `totalCount`, `page`, `pageSize`, `totalPages`, `displayCurrency`.

### GET `/api/storefront/products/{id}`
- **Query:** `preferredCurrency` opsiyonel.
- **Response (`GetStorefrontProductResponse`):** Ürün vitrini için sadeleştirilmiş detay:
  - Alanlar: `id`, `title`, `description`, `shortDescription`, `slug`, `sku`, `price`, `compareAtPrice`, `currency`, `inventoryQuantity`, `isInStock`, `allowBackorder`, `weight`, `weightUnit`, `requiresShipping`, `isDigital`, `isTaxable`, `metaTitle`, `metaDescription`, `metaKeywords`, `vendor`, `productType`, `images[]`, `categories[]`, `variants[]`, `options[]`, `tags[]`, `createdAt`.
  - DTO içerikleri: `StorefrontImageDto`, `StorefrontCategoryDto`, `StorefrontVariantDto`, `StorefrontOptionDto`.

### GET `/api/storefront/categories`
- **Response (`GetStorefrontCategoriesResponse`):** `categories[]` dizisi; her `StorefrontCategoryDto` aşağıdaki alanları sağlar: `id`, `name`, `slug`, `description`, `imageUrl`, `parentCategoryId`, `displayOrder`, `subCategories[]`.

---

## 3. Vergi Uçları – `TaxController`

Kaynak: `src/Tinisoft.Products.API/Controllers/TaxController.cs`

### POST `/api/tax/calculate`
- **Amaç:** Fiyat + bağlam verilip toplam vergi hesaplar.
- **Body (`CalculateTaxCommand`):**

| Alan | Tip | Açıklama |
| --- | --- | --- |
| `productId` | GUID? | Ürün ID (opsiyonel). |
| `categoryId` | GUID? | Kategori bazlı vergi için. |
| `productType` | string? | Ek sınıflandırma. |
| `price`* | decimal | Vergi öncesi birim fiyat. |
| `quantity` | int | Varsayılan `1`. |
| `countryCode` | string? | ISO ülke; varsayılan `TR`. |
| `region` | string? | İl/eyalet. |
| `taxRateId` | GUID? | Belirli vergi oranını zorlamak için. |

- **Response (`CalculateTaxResponse`):**

| Alan | Tip | Açıklama |
| --- | --- | --- |
| `subtotal` | decimal | Vergi öncesi toplam. |
| `taxAmount` | decimal | Toplam vergi. |
| `total` | decimal | Vergi dahil toplam. |
| `taxDetails[]` | TaxDetailDto[] | Her vergi kalemi: `taxRateId`, `taxName`, `taxCode`, `rate`, `taxableAmount`, `taxAmount`, `type`. |

### GET `/api/tax/rates`
- **Query:** `isActive` (bool?).
- **Response:** `TaxRateDto[]` – alanlar `id`, `name`, `code`, `rate`, `type`, `taxCode`, `exciseTaxCode`, `productServiceCode`, `isIncludedInPrice`, `eInvoiceTaxType`, `isExempt`, `exemptionReason`, `isActive`, `description`.

### POST `/api/tax/rates`
- **Body (`CreateTaxRateCommand`):** `name`, `code`, `rate`, `type`, `taxCode`, `exciseTaxCode`, `productServiceCode`, `isIncludedInPrice`, `eInvoiceTaxType`, `isExempt`, `exemptionReason`, `description`.
- **Response:** `CreateTaxRateResponse` → `taxRateId`, `name`.

### PUT `/api/tax/rates/{id}`
- **Body (`UpdateTaxRateCommand`):** `taxRateId` (controller set eder), `name`, `code`, `rate`, `type`, `taxCode`, `exciseTaxCode`, `productServiceCode`, `isIncludedInPrice`, `eInvoiceTaxType`, `isExempt`, `exemptionReason`, `isActive`, `description`.
- **Response:** `UpdateTaxRateResponse` → `taxRateId`, `name`.

### DELETE `/api/tax/rates/{id}`
- **Response:** `204 No Content`.

---

## Notlar & Kontroller
- Tüm command/response modelleri `Tinisoft.Application` katmanında tutulur; UI tarafında tip güvenliği için aynı sözleşmeleri paylaşmak üzere `Tinisoft.Shared` projeye taşınması planlanıyor.
- Public uçlar multi-currency dönüşümlerini backend içinde çözümler; `preferredCurrency` verilirse buna göre fallback yapılır.
- Ürün oluşturma/güncelleme isteklerinde gönderilmeyen koleksiyonlar boş kabul edilir; delta merge davranışı tekil handler içinde belirlenmiştir (tam sync için tüm listeleri gönderin).


