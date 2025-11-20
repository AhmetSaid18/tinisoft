## Tinisoft Platform API Reference
Toplam 111 endpoint. JSON payloadlar System.Text.Json varsayılan camelCase serializer ile döner. Tüm tenant servislerinde `Authorization: Bearer <jwt>` ve `X-Tenant-Id` header'ı gereklidir (public feeds hariç).

### Tinisoft.API
Backoffice endpoints for tenants: auth, catalog, pricing, inventory, coupons, templates.

#### GET `/api/admin/statistics`
Controller `AdminController` • Action `GetSystemStatistics`
Get system statistics.

**Response** `GetSystemStatisticsResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| totalUsers | `int` | Total users |
| totalTenants | `int` | Total tenants |
| activeTenants | `int` | Active tenants |
| totalProducts | `int` | Total products |
| totalOrders | `int` | Total orders |
| totalRevenue | `decimal` | Total revenue |
| monthlyRevenue | `decimal` | Monthly revenue |
| systemAdminCount | `int` | System admin count |
| tenantAdminCount | `int` | Tenant admin count |
| customerCount | `int` | Customer count |
Örnek Yanıt:
```json
{
  "totalUsers": 0,
  "totalTenants": 0,
  "activeTenants": 0,
  "totalProducts": 0,
  "totalOrders": 0,
  "totalRevenue": 0,
  "monthlyRevenue": 0,
  "systemAdminCount": 0,
  "tenantAdminCount": 0,
  "customerCount": 0
}
```
---

#### GET `/api/admin/templates`
Controller `AdminTemplatesController` • Action `GetAllTemplates`
Get all templates.

**Response** `GetAllTemplatesResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| templates | `List<TemplateDto>` | Templates |
Örnek Yanıt:
```json
{
  "templates": [
    {}
  ]
}
```
---

#### POST `/api/admin/templates`
Controller `AdminTemplatesController` • Action `CreateTemplate`
Create template.

Request body `CreateTemplateCommand` (detaylı şema bulunamadı).

**Response** `CreateTemplateResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| templateId | `Guid` | Template id |
| code | `string` | Code |
| name | `string` | Name |
| message | `string` | Message |
Örnek Yanıt:
```json
{
  "templateId": "11111111-1111-1111-1111-111111111111",
  "code": "string",
  "name": "string",
  "message": "string"
}
```
---

#### DELETE `/api/admin/templates/{id}`
Controller `AdminTemplatesController` • Action `DeleteTemplate`
Delete template.

**Path Parametreleri**
| Ad | Tip | Açıklama |
| --- | --- | --- |
| id | `Guid` | Id |

**Response** `DeleteTemplateResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| templateId | `Guid` | Template id |
| message | `string` | Message |
Örnek Yanıt:
```json
{
  "templateId": "11111111-1111-1111-1111-111111111111",
  "message": "string"
}
```
---

#### PUT `/api/admin/templates/{id}`
Controller `AdminTemplatesController` • Action `UpdateTemplate`
Update template.

**Path Parametreleri**
| Ad | Tip | Açıklama |
| --- | --- | --- |
| id | `Guid` | Id |

Request body `UpdateTemplateCommand` (detaylı şema bulunamadı).

**Response** `UpdateTemplateResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| templateId | `Guid` | Template id |
| code | `string` | Code |
| message | `string` | Message |
Örnek Yanıt:
```json
{
  "templateId": "11111111-1111-1111-1111-111111111111",
  "code": "string",
  "message": "string"
}
```
---

#### PATCH `/api/admin/templates/{id}/toggle-active`
Controller `AdminTemplatesController` • Action `ToggleTemplateActive`
Toggle template active.

**Path Parametreleri**
| Ad | Tip | Açıklama |
| --- | --- | --- |
| id | `Guid` | Id |

Request body `ToggleTemplateActiveCommand` (detaylı şema bulunamadı).

**Response** `ToggleTemplateActiveResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| templateId | `Guid` | Template id |
| isActive | `bool` | Is active |
| message | `string` | Message |
Örnek Yanıt:
```json
{
  "templateId": "11111111-1111-1111-1111-111111111111",
  "isActive": true,
  "message": "string"
}
```
---

#### POST `/api/auth/login`
Controller `AuthController` • Action `Login`
Login.

Request body `LoginCommand` (detaylı şema bulunamadı).

**Response** `LoginResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| userId | `Guid` | User id |
| email | `string` | Email |
| token | `string` | Token |
| tenantId | `Guid?` | Tenant id |
| systemRole | `string` | System role |
| tenantRole | `string?` | Tenant role |
Örnek Yanıt:
```json
{
  "userId": "11111111-1111-1111-1111-111111111111",
  "email": "string",
  "token": "string",
  "tenantId": "11111111-1111-1111-1111-111111111111",
  "systemRole": "string",
  "tenantRole": "string"
}
```
---

#### POST `/api/auth/register`
Controller `AuthController` • Action `Register`
Register.

Request body `RegisterCommand` (detaylı şema bulunamadı).

**Response** `RegisterResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| userId | `Guid` | User id |
| email | `string` | Email |
| token | `string` | Token |
| tenantId | `Guid?` | Tenant id |
| systemRole | `string` | System role |
Örnek Yanıt:
```json
{
  "userId": "11111111-1111-1111-1111-111111111111",
  "email": "string",
  "token": "string",
  "tenantId": "11111111-1111-1111-1111-111111111111",
  "systemRole": "string"
}
```
---

#### GET `/api/coupons`
Controller `CouponsController` • Action `GetCoupons`
Get coupons.

**Query Parametreleri**
| Ad | Tip | Açıklama |
| --- | --- | --- |
| query | `GetCouponsQuery` | Query |

**Response** `GetCouponsResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| coupons | `List<CouponDto>` | Coupons |
| totalCount | `int` | Total count |
| page | `int` | Page |
| pageSize | `int` | Page size |
Örnek Yanıt:
```json
{
  "coupons": [
    {}
  ],
  "totalCount": 0,
  "page": 0,
  "pageSize": 0
}
```
---

#### POST `/api/coupons`
Controller `CouponsController` • Action `CreateCoupon`
Create coupon.

Request body `CreateCouponCommand` (detaylı şema bulunamadı).

**Response** `CreateCouponResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| couponId | `Guid` | Coupon id |
| code | `string` | Code |
Örnek Yanıt:
```json
{
  "couponId": "11111111-1111-1111-1111-111111111111",
  "code": "string"
}
```
---

#### DELETE `/api/coupons/{id}`
Controller `CouponsController` • Action `DeleteCoupon`
Delete coupon.

**Path Parametreleri**
| Ad | Tip | Açıklama |
| --- | --- | --- |
| id | `Guid` | Id |

**Response** `DeleteCouponResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| success | `bool` | Success |
Örnek Yanıt:
```json
{
  "success": true
}
```
---

#### GET `/api/coupons/{id}`
Controller `CouponsController` • Action `GetCoupon`
Get coupon.

**Path Parametreleri**
| Ad | Tip | Açıklama |
| --- | --- | --- |
| id | `Guid` | Id |

**Response** `GetCouponResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| id | `Guid` | Id |
| code | `string` | Code |
| name | `string` | Name |
| description | `string?` | Description |
| discountType | `string` | Discount type |
| discountValue | `decimal` | Discount value |
| currency | `string` | Currency |
| minOrderAmount | `decimal?` | Min order amount |
| maxDiscountAmount | `decimal?` | Max discount amount |
| maxUsageCount | `int?` | Max usage count |
| maxUsagePerCustomer | `int?` | Max usage per customer |
| validFrom | `DateTime?` | Valid from |
| validTo | `DateTime?` | Valid to |
| appliesToAllProducts | `bool` | Applies to all products |
| applicableProductIds | `List<Guid>` | Applicable product ids |
| applicableCategoryIds | `List<Guid>` | Applicable category ids |
| excludedProductIds | `List<Guid>` | Excluded product ids |
| appliesToAllCustomers | `bool` | Applies to all customers |
| applicableCustomerIds | `List<Guid>` | Applicable customer ids |
| isActive | `bool` | Is active |
| usageCount | `int` | Usage count |
| createdAt | `DateTime` | Created at |
| updatedAt | `DateTime?` | Updated at |
Örnek Yanıt:
```json
{
  "id": "11111111-1111-1111-1111-111111111111",
  "code": "string",
  "name": "string",
  "description": "string",
  "discountType": "string",
  "discountValue": 0,
  "currency": "string",
  "minOrderAmount": 0,
  "maxDiscountAmount": 0,
  "maxUsageCount": 0,
  "maxUsagePerCustomer": 0,
  "validFrom": "2024-01-01T00:00:00Z",
  "validTo": "2024-01-01T00:00:00Z",
  "appliesToAllProducts": true,
  "applicableProductIds": [
    "11111111-1111-1111-1111-111111111111"
  ],
  "applicableCategoryIds": [
    "11111111-1111-1111-1111-111111111111"
  ],
  "excludedProductIds": [
    "11111111-1111-1111-1111-111111111111"
  ],
  "appliesToAllCustomers": true,
  "applicableCustomerIds": [
    "11111111-1111-1111-1111-111111111111"
  ],
  "isActive": true,
  "usageCount": 0,
  "createdAt": "2024-01-01T00:00:00Z",
  "updatedAt": "2024-01-01T00:00:00Z"
}
```
---

#### PUT `/api/coupons/{id}`
Controller `CouponsController` • Action `UpdateCoupon`
Update coupon.

**Path Parametreleri**
| Ad | Tip | Açıklama |
| --- | --- | --- |
| id | `Guid` | Id |

Request body `UpdateCouponCommand` (detaylı şema bulunamadı).

**Response** `UpdateCouponResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| couponId | `Guid` | Coupon id |
| success | `bool` | Success |
Örnek Yanıt:
```json
{
  "couponId": "11111111-1111-1111-1111-111111111111",
  "success": true
}
```
---

#### GET `/api/coupons/{id}/statistics`
Controller `CouponsController` • Action `GetCouponStatistics`
Get coupon statistics.

**Path Parametreleri**
| Ad | Tip | Açıklama |
| --- | --- | --- |
| id | `Guid` | Id |

**Response** `GetCouponStatisticsResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| couponId | `Guid` | Coupon id |
| code | `string` | Code |
| name | `string` | Name |
| totalUsageCount | `int` | Total usage count |
| uniqueCustomerCount | `int` | Unique customer count |
| totalDiscountAmount | `decimal` | Total discount amount |
| averageDiscountAmount | `decimal` | Average discount amount |
| firstUsedAt | `DateTime?` | First used at |
| lastUsedAt | `DateTime?` | Last used at |
| recentUsages | `List<CouponUsageDetailDto>` | Recent usages |
Örnek Yanıt:
```json
{
  "couponId": "11111111-1111-1111-1111-111111111111",
  "code": "string",
  "name": "string",
  "totalUsageCount": 0,
  "uniqueCustomerCount": 0,
  "totalDiscountAmount": 0,
  "averageDiscountAmount": 0,
  "firstUsedAt": "2024-01-01T00:00:00Z",
  "lastUsedAt": "2024-01-01T00:00:00Z",
  "recentUsages": [
    {}
  ]
}
```
---

#### POST `/api/Inventory/adjust`
Controller `InventoryController` • Action `AdjustStock`
Adjust stock.

Request body `AdjustStockCommand` (detaylı şema bulunamadı).

**Response** `AdjustStockResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| productId | `Guid` | Product id |
| variantId | `Guid?` | Variant id |
| oldQuantity | `int` | Old quantity |
| newQuantity | `int` | New quantity |
Örnek Yanıt:
```json
{
  "productId": "11111111-1111-1111-1111-111111111111",
  "variantId": "11111111-1111-1111-1111-111111111111",
  "oldQuantity": 0,
  "newQuantity": 0
}
```
---

#### GET `/api/Inventory/alerts/low-stock`
Controller `InventoryController` • Action `GetLowStockAlerts`
Get low stock alerts.

**Query Parametreleri**
| Ad | Tip | Açıklama |
| --- | --- | --- |
| query | `GetLowStockAlertsQuery` | Query |

**Response** `GetLowStockAlertsResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| alerts | `List<LowStockAlertDto>` | Alerts |
| totalCount | `int` | Total count |
Örnek Yanıt:
```json
{
  "alerts": [
    {}
  ],
  "totalCount": 0
}
```
---

#### POST `/api/Inventory/count`
Controller `InventoryController` • Action `CountInventory`
Count inventory.

Request body `CountInventoryCommand` (detaylı şema bulunamadı).

**Response** `CountInventoryResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| productInventoryId | `Guid` | Product inventory id |
| previousQuantity | `int` | Previous quantity |
| countedQuantity | `int` | Counted quantity |
| difference | `int` | Difference |
| success | `bool` | Success |
| message | `string?` | Message |
Örnek Yanıt:
```json
{
  "productInventoryId": "11111111-1111-1111-1111-111111111111",
  "previousQuantity": 0,
  "countedQuantity": 0,
  "difference": 0,
  "success": true,
  "message": "string"
}
```
---

#### POST `/api/Inventory/locations`
Controller `InventoryController` • Action `CreateWarehouseLocation`
Create warehouse location.

Request body `CreateWarehouseLocationCommand` (detaylı şema bulunamadı).

**Response** `CreateWarehouseLocationResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| locationId | `Guid` | Location id |
| locationCode | `string` | Location code |
| message | `string` | Message |
Örnek Yanıt:
```json
{
  "locationId": "11111111-1111-1111-1111-111111111111",
  "locationCode": "string",
  "message": "string"
}
```
---

#### GET `/api/Inventory/movements`
Controller `InventoryController` • Action `GetStockMovements`
Get stock movements.

**Query Parametreleri**
| Ad | Tip | Açıklama |
| --- | --- | --- |
| query | `GetStockMovementsQuery` | Query |

**Response** `GetStockMovementsResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| movements | `List<StockMovementDto>` | Movements |
| totalCount | `int` | Total count |
| page | `int` | Page |
| pageSize | `int` | Page size |
Örnek Yanıt:
```json
{
  "movements": [
    {}
  ],
  "totalCount": 0,
  "page": 0,
  "pageSize": 0
}
```
---

#### GET `/api/Inventory/orders/{orderId}/picking-list`
Controller `InventoryController` • Action `GetPickingList`
Get picking list.

**Path Parametreleri**
| Ad | Tip | Açıklama |
| --- | --- | --- |
| orderId | `Guid` | Order id |

**Response** `GetPickingListResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| orderId | `Guid` | Order id |
| orderNumber | `string` | Order number |
| items | `List<PickingItem>` | Items |
Örnek Yanıt:
```json
{
  "orderId": "11111111-1111-1111-1111-111111111111",
  "orderNumber": "string",
  "items": [
    {}
  ]
}
```
---

#### POST `/api/Inventory/pick`
Controller `InventoryController` • Action `PickOrderItem`
Pick order item.

Request body `PickOrderItemCommand` (detaylı şema bulunamadı).

**Response** `PickOrderItemResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| orderItemId | `Guid` | Order item id |
| success | `bool` | Success |
| message | `string?` | Message |
Örnek Yanıt:
```json
{
  "orderItemId": "11111111-1111-1111-1111-111111111111",
  "success": true,
  "message": "string"
}
```
---

#### GET `/api/Inventory/products/{productId}`
Controller `InventoryController` • Action `GetStockLevel`
Get stock level.

**Path Parametreleri**
| Ad | Tip | Açıklama |
| --- | --- | --- |
| productId | `Guid` | Product id |

**Query Parametreleri**
| Ad | Tip | Açıklama |
| --- | --- | --- |
| variantId | `Guid?` | Variant id |

**Response** `GetStockLevelResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| productId | `Guid` | Product id |
| variantId | `Guid?` | Variant id |
| quantity | `int?` | Quantity |
| trackInventory | `bool` | Track inventory |
| isLowStock | `bool` | Is low stock |
Örnek Yanıt:
```json
{
  "productId": "11111111-1111-1111-1111-111111111111",
  "variantId": "11111111-1111-1111-1111-111111111111",
  "quantity": 0,
  "trackInventory": true,
  "isLowStock": true
}
```
---

#### POST `/api/Inventory/transfer`
Controller `InventoryController` • Action `TransferStock`
Transfer stock.

Request body `TransferStockCommand` (detaylı şema bulunamadı).

**Response** `TransferStockResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| success | `bool` | Success |
| message | `string?` | Message |
| fromInventoryId | `Guid?` | From inventory id |
| toInventoryId | `Guid?` | To inventory id |
Örnek Yanıt:
```json
{
  "success": true,
  "message": "string",
  "fromInventoryId": "11111111-1111-1111-1111-111111111111",
  "toInventoryId": "11111111-1111-1111-1111-111111111111"
}
```
---

#### GET `/api/Inventory/warehouse-stock`
Controller `InventoryController` • Action `GetWarehouseStock`
Get warehouse stock.

**Query Parametreleri**
| Ad | Tip | Açıklama |
| --- | --- | --- |
| query | `GetWarehouseStockQuery` | Query |

**Response** `GetWarehouseStockResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| items | `List<WarehouseStockDto>` | Items |
| totalCount | `int` | Total count |
| page | `int` | Page |
| pageSize | `int` | Page size |
Örnek Yanıt:
```json
{
  "items": [
    {}
  ],
  "totalCount": 0,
  "page": 0,
  "pageSize": 0
}
```
---

#### POST `/api/Payments/callback/paytr`
Controller `PaymentsController` • Action `PayTRCallback`
Pay t r callback.

**Form Parametreleri**
| Ad | Tip | Açıklama |
| --- | --- | --- |
| data | `Dictionary<string, string>` | Data |

**Response** `IActionResult`
İçerik custom `IActionResult` ile dönüyor.

---

#### POST `/api/Payments/process`
Controller `PaymentsController` • Action `ProcessPayment`
Process payment.

Request body `ProcessPaymentCommand` (detaylı şema bulunamadı).

**Response** `ProcessPaymentResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| success | `bool` | Success |
| paymentToken | `string?` | Payment token |
| paymentReference | `string?` | Payment reference |
| errorMessage | `string?` | Error message |
| redirectUrl | `string?` | Redirect url |
Örnek Yanıt:
```json
{
  "success": true,
  "paymentToken": "string",
  "paymentReference": "string",
  "errorMessage": "string",
  "redirectUrl": "string"
}
```
---

#### POST `/api/Payments/verify`
Controller `PaymentsController` • Action `VerifyPayment`
Verify payment.

Request body `VerifyPaymentCommand` (detaylı şema bulunamadı).

**Response** `VerifyPaymentResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| isValid | `bool` | Is valid |
| isPaid | `bool` | Is paid |
| errorMessage | `string?` | Error message |
Örnek Yanıt:
```json
{
  "isValid": true,
  "isPaid": true,
  "errorMessage": "string"
}
```
---

#### GET `/api/Products`
Controller `ProductsController` • Action `GetProducts`
Get products.

**Query Parametreleri**
| Ad | Tip | Açıklama |
| --- | --- | --- |
| query | `GetProductsQuery` | Query |

**Response** `GetProductsResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| items | `List<ProductListItemDto>` | Items |
| totalCount | `int` | Total count |
| page | `int` | Page |
| pageSize | `int` | Page size |
Örnek Yanıt:
```json
{
  "items": [
    {}
  ],
  "totalCount": 0,
  "page": 0,
  "pageSize": 0
}
```
---

#### POST `/api/Products`
Controller `ProductsController` • Action `CreateProduct`
Create product.

Request body `CreateProductCommand` (detaylı şema bulunamadı).

**Response** `CreateProductResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| productId | `Guid` | Product id |
| title | `string` | Title |
Örnek Yanıt:
```json
{
  "productId": "11111111-1111-1111-1111-111111111111",
  "title": "string"
}
```
---

#### GET `/api/Products/cursor`
Controller `ProductsController` • Action `GetProductsCursor`
Get products cursor.

**Query Parametreleri**
| Ad | Tip | Açıklama |
| --- | --- | --- |
| query | `GetProductsCursorQuery` | Query |

**Response** `GetProductsCursorResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| items | `List<ProductListItemDto>` | Items |
| nextCursor | `string?` | Next cursor |
| previousCursor | `string?` | Previous cursor |
| hasNextPage | `bool` | Has next page |
| hasPreviousPage | `bool` | Has previous page |
| limit | `int` | Limit |
Örnek Yanıt:
```json
{
  "items": [
    {}
  ],
  "nextCursor": "string",
  "previousCursor": "string",
  "hasNextPage": true,
  "hasPreviousPage": true,
  "limit": 0
}
```
---

#### DELETE `/api/Products/{id}`
Controller `ProductsController` • Action `DeleteProduct`
Delete product.

**Path Parametreleri**
| Ad | Tip | Açıklama |
| --- | --- | --- |
| id | `Guid` | Id |

**Response** `IActionResult`
İçerik custom `IActionResult` ile dönüyor.

---

#### GET `/api/Products/{id}`
Controller `ProductsController` • Action `GetProduct`
Get product.

**Path Parametreleri**
| Ad | Tip | Açıklama |
| --- | --- | --- |
| id | `Guid` | Id |

**Response** `GetProductResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| id | `Guid` | Id |
| title | `string` | Title |
| description | `string?` | Description |
| shortDescription | `string?` | Short description |
| slug | `string` | Slug |
| sKU | `string?` | S k u |
| barcode | `string?` | Barcode |
| gTIN | `string?` | G t i n |
| price | `decimal` | Price |
| compareAtPrice | `decimal?` | Compare at price |
| costPerItem | `decimal` | Cost per item |
| currency | `string` | Currency |
| status | `string` | Status |
| trackInventory | `bool` | Track inventory |
| inventoryQuantity | `int?` | Inventory quantity |
| allowBackorder | `bool` | Allow backorder |
| weight | `decimal?` | Weight |
| weightUnit | `string?` | Weight unit |
| length | `decimal?` | Length |
| width | `decimal?` | Width |
| height | `decimal?` | Height |
| requiresShipping | `bool` | Requires shipping |
| isDigital | `bool` | Is digital |
| isTaxable | `bool` | Is taxable |
| taxCode | `string?` | Tax code |
| metaTitle | `string?` | Meta title |
| metaDescription | `string?` | Meta description |
| metaKeywords | `string?` | Meta keywords |
| vendor | `string?` | Vendor |
| productType | `string?` | Product type |
| publishedScope | `string` | Published scope |
| templateSuffix | `string?` | Template suffix |
| isGiftCard | `bool` | Is gift card |
| inventoryManagement | `string?` | Inventory management |
| fulfillmentService | `string?` | Fulfillment service |
| countryOfOrigin | `string?` | Country of origin |
| hSCode | `string?` | H s code |
| minQuantity | `int?` | Min quantity |
| maxQuantity | `int?` | Max quantity |
| incrementQuantity | `int?` | Increment quantity |
| shippingClass | `string?` | Shipping class |
| barcodeFormat | `string?` | Barcode format |
| unitPrice | `decimal?` | Unit price |
| unitPriceUnit | `string?` | Unit price unit |
| chargeTaxes | `bool` | Charge taxes |
| taxCategory | `string?` | Tax category |
| defaultInventoryLocationId | `Guid?` | Default inventory location id |
| isActive | `bool` | Is active |
| publishedAt | `DateTime?` | Published at |
| images | `List<ImageDto>` | Images |
| categories | `List<CategoryDto>` | Categories |
| variants | `List<VariantDto>` | Variants |
| options | `List<OptionDto>` | Options |
| metafields | `List<MetafieldDto>` | Metafields |
| tags | `List<string>` | Tags |
| collections | `List<string>` | Collections |
| salesChannels | `List<string>` | Sales channels |
| videoUrl | `string?` | Video url |
| videoThumbnailUrl | `string?` | Video thumbnail url |
| customFields | `Dictionary<string, object>?` | Custom fields |
| createdAt | `DateTime` | Created at |
| updatedAt | `DateTime?` | Updated at |
Örnek Yanıt:
```json
{
  "id": "11111111-1111-1111-1111-111111111111",
  "title": "string",
  "description": "string",
  "shortDescription": "string",
  "slug": "string",
  "sKU": "string",
  "barcode": "string",
  "gTIN": "string",
  "price": 0,
  "compareAtPrice": 0,
  "costPerItem": 0,
  "currency": "string",
  "status": "string",
  "trackInventory": true,
  "inventoryQuantity": 0,
  "allowBackorder": true,
  "weight": 0,
  "weightUnit": "string",
  "length": 0,
  "width": 0,
  "height": 0,
  "requiresShipping": true,
  "isDigital": true,
  "isTaxable": true,
  "taxCode": "string",
  "metaTitle": "string",
  "metaDescription": "string",
  "metaKeywords": "string",
  "vendor": "string",
  "productType": "string",
  "publishedScope": "string",
  "templateSuffix": "string",
  "isGiftCard": true,
  "inventoryManagement": "string",
  "fulfillmentService": "string",
  "countryOfOrigin": "string",
  "hSCode": "string",
  "minQuantity": 0,
  "maxQuantity": 0,
  "incrementQuantity": 0,
  "shippingClass": "string",
  "barcodeFormat": "string",
  "unitPrice": 0,
  "unitPriceUnit": "string",
  "chargeTaxes": true,
  "taxCategory": "string",
  "defaultInventoryLocationId": "11111111-1111-1111-1111-111111111111",
  "isActive": true,
  "publishedAt": "2024-01-01T00:00:00Z",
  "images": [
    {}
  ],
  "categories": [
    {}
  ],
  "variants": [
    {}
  ],
  "options": [
    {}
  ],
  "metafields": [
    {}
  ],
  "tags": [
    "string"
  ],
  "collections": [
    "string"
  ],
  "salesChannels": [
    "string"
  ],
  "videoUrl": "string",
  "videoThumbnailUrl": "string",
  "customFields": {
    "key": "value"
  },
  "createdAt": "2024-01-01T00:00:00Z",
  "updatedAt": "2024-01-01T00:00:00Z"
}
```
---

#### PUT `/api/Products/{id}`
Controller `ProductsController` • Action `UpdateProduct`
Update product.

**Path Parametreleri**
| Ad | Tip | Açıklama |
| --- | --- | --- |
| id | `Guid` | Id |

Request body `UpdateProductCommand` (detaylı şema bulunamadı).

**Response** `UpdateProductResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| productId | `Guid` | Product id |
| title | `string` | Title |
Örnek Yanıt:
```json
{
  "productId": "11111111-1111-1111-1111-111111111111",
  "title": "string"
}
```
---

#### GET `/api/public/bootstrap`
Controller `PublicController` • Action `Bootstrap`
Bootstrap.

**Response** `GetBootstrapDataResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| tenantId | `Guid` | Tenant id |
| tenantName | `string` | Tenant name |
| templateKey | `string?` | Template key |
| templateVersion | `int?` | Template version |
| theme | `BootstrapTheme` | Theme |
| settings | `BootstrapSettings` | Settings |
Örnek Yanıt:
```json
{
  "tenantId": "11111111-1111-1111-1111-111111111111",
  "tenantName": "string",
  "templateKey": "string",
  "templateVersion": 0,
  "theme": {
    "primaryColor": "string",
    "secondaryColor": "string",
    "backgroundColor": "string",
    "textColor": "string",
    "linkColor": "string",
    "buttonColor": "string",
    "buttonTextColor": "string",
    "fontFamily": "string",
    "headingFontFamily": "string",
    "baseFontSize": 0,
    "layoutSettings": {
      "key": "value"
    }
  },
  "settings": {
    "logoUrl": "string",
    "faviconUrl": "string",
    "siteTitle": "string",
    "siteDescription": "string",
    "facebookUrl": "string",
    "instagramUrl": "string",
    "twitterUrl": "string",
    "linkedInUrl": "string",
    "youTubeUrl": "string",
    "tikTokUrl": "string",
    "pinterestUrl": "string",
    "whatsAppNumber": "string",
    "telegramUsername": "string",
    "email": "string",
    "phone": "string",
    "address": "string",
    "city": "string",
    "country": "string"
  }
}
```
---

#### GET `/api/public/feeds/cimri.xml`
Controller `PublicFeedsController` • Action `GetCimriFeed`
Get cimri feed.

**Response** `IActionResult`
İçerik custom `IActionResult` ile dönüyor.

---

#### GET `/api/public/feeds/google-shopping.xml`
Controller `PublicFeedsController` • Action `GetGoogleShoppingFeed`
Get google shopping feed.

**Response** `IActionResult`
İçerik custom `IActionResult` ile dönüyor.

---

#### GET `/api/public/feeds/products.xml`
Controller `PublicFeedsController` • Action `GetCustomFeed`
Get custom feed.

**Query Parametreleri**
| Ad | Tip | Açıklama |
| --- | --- | --- |
| format | `string?` | Format |

**Response** `IActionResult`
İçerik custom `IActionResult` ile dönüyor.

---

#### GET `/api/Resellers`
Controller `ResellersController` • Action `GetResellers`
Get resellers.

**Query Parametreleri**
| Ad | Tip | Açıklama |
| --- | --- | --- |
| query | `GetResellersQuery` | Query |

**Response** `GetResellersResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| resellers | `List<ResellerDto>` | Resellers |
| totalCount | `int` | Total count |
| page | `int` | Page |
| pageSize | `int` | Page size |
Örnek Yanıt:
```json
{
  "resellers": [
    {}
  ],
  "totalCount": 0,
  "page": 0,
  "pageSize": 0
}
```
---

#### POST `/api/Resellers`
Controller `ResellersController` • Action `CreateReseller`
Create reseller.

Request body `CreateResellerCommand` (detaylı şema bulunamadı).

**Response** `CreateResellerResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| resellerId | `Guid` | Reseller id |
| companyName | `string` | Company name |
| email | `string` | Email |
Örnek Yanıt:
```json
{
  "resellerId": "11111111-1111-1111-1111-111111111111",
  "companyName": "string",
  "email": "string"
}
```
---

#### POST `/api/Resellers/{resellerId}/prices`
Controller `ResellersController` • Action `CreateResellerPrice`
Create reseller price.

**Path Parametreleri**
| Ad | Tip | Açıklama |
| --- | --- | --- |
| resellerId | `Guid` | Reseller id |

Request body `CreateResellerPriceCommand` (detaylı şema bulunamadı).

**Response** `CreateResellerPriceResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| resellerPriceId | `Guid` | Reseller price id |
| resellerId | `Guid` | Reseller id |
| productId | `Guid` | Product id |
| price | `decimal` | Price |
Örnek Yanıt:
```json
{
  "resellerPriceId": "11111111-1111-1111-1111-111111111111",
  "resellerId": "11111111-1111-1111-1111-111111111111",
  "productId": "11111111-1111-1111-1111-111111111111",
  "price": 0
}
```
---

#### POST `/api/reviews`
Controller `ReviewsController` • Action `CreateReview`
Create review.

Request body `CreateReviewCommand` (detaylı şema bulunamadı).

**Response** `CreateReviewResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| reviewId | `Guid` | Review id |
| isApproved | `bool` | Is approved |
| message | `string` | Message |
Örnek Yanıt:
```json
{
  "reviewId": "11111111-1111-1111-1111-111111111111",
  "isApproved": true,
  "message": "string"
}
```
---

#### GET `/api/reviews/product/{productId}`
Controller `ReviewsController` • Action `GetProductReviews`
Get product reviews.

**Path Parametreleri**
| Ad | Tip | Açıklama |
| --- | --- | --- |
| productId | `Guid` | Product id |

**Query Parametreleri**
| Ad | Tip | Açıklama |
| --- | --- | --- |
| page | `int` | Page |
| pageSize | `int` | Page size |
| sortBy | `string?` | Sort by |
| sortOrder | `string?` | Sort order |
| minRating | `int?` | Min rating |
| maxRating | `int?` | Max rating |
| isVerifiedPurchase | `bool?` | Is verified purchase |
| hasReply | `bool?` | Has reply |
| onlyWithImages | `bool?` | Only with images |

**Response** `GetProductReviewsResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| items | `List<ProductReviewDto>` | Items |
| totalCount | `int` | Total count |
| page | `int` | Page |
| pageSize | `int` | Page size |
| statistics | `ReviewStatisticsDto` | Statistics |
Örnek Yanıt:
```json
{
  "items": [
    {}
  ],
  "totalCount": 0,
  "page": 0,
  "pageSize": 0,
  "statistics": {
    "averageRating": 0,
    "totalReviews": 0,
    "rating1Count": 0,
    "rating2Count": 0,
    "rating3Count": 0,
    "rating4Count": 0,
    "rating5Count": 0,
    "verifiedPurchaseCount": 0,
    "withImagesCount": 0,
    "withReplyCount": 0
  }
}
```
---

#### DELETE `/api/reviews/{id}`
Controller `ReviewsController` • Action `DeleteReview`
Delete review.

**Path Parametreleri**
| Ad | Tip | Açıklama |
| --- | --- | --- |
| id | `Guid` | Id |

**Response** `DeleteReviewResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| reviewId | `Guid` | Review id |
| success | `bool` | Success |
| message | `string` | Message |
Örnek Yanıt:
```json
{
  "reviewId": "11111111-1111-1111-1111-111111111111",
  "success": true,
  "message": "string"
}
```
---

#### PUT `/api/reviews/{id}`
Controller `ReviewsController` • Action `UpdateReview`
Update review.

**Path Parametreleri**
| Ad | Tip | Açıklama |
| --- | --- | --- |
| id | `Guid` | Id |

Request body `UpdateReviewCommand` (detaylı şema bulunamadı).

**Response** `UpdateReviewResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| reviewId | `Guid` | Review id |
| message | `string` | Message |
Örnek Yanıt:
```json
{
  "reviewId": "11111111-1111-1111-1111-111111111111",
  "message": "string"
}
```
---

#### POST `/api/reviews/{id}/approve`
Controller `ReviewsController` • Action `ApproveReview`
Approve review.

**Path Parametreleri**
| Ad | Tip | Açıklama |
| --- | --- | --- |
| id | `Guid` | Id |

Request body `ApproveReviewCommand` (detaylı şema bulunamadı).

**Response** `ApproveReviewResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| reviewId | `Guid` | Review id |
| isApproved | `bool` | Is approved |
| isPublished | `bool` | Is published |
| message | `string` | Message |
Örnek Yanıt:
```json
{
  "reviewId": "11111111-1111-1111-1111-111111111111",
  "isApproved": true,
  "isPublished": true,
  "message": "string"
}
```
---

#### POST `/api/reviews/{id}/reply`
Controller `ReviewsController` • Action `ReplyToReview`
Reply to review.

**Path Parametreleri**
| Ad | Tip | Açıklama |
| --- | --- | --- |
| id | `Guid` | Id |

Request body `ReplyToReviewCommand` (detaylı şema bulunamadı).

**Response** `ReplyToReviewResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| reviewId | `Guid` | Review id |
| replyText | `string` | Reply text |
| repliedAt | `DateTime` | Replied at |
| message | `string` | Message |
Örnek Yanıt:
```json
{
  "reviewId": "11111111-1111-1111-1111-111111111111",
  "replyText": "string",
  "repliedAt": "2024-01-01T00:00:00Z",
  "message": "string"
}
```
---

#### POST `/api/reviews/{id}/vote`
Controller `ReviewsController` • Action `VoteReview`
Vote review.

**Path Parametreleri**
| Ad | Tip | Açıklama |
| --- | --- | --- |
| id | `Guid` | Id |

Request body `VoteReviewCommand` (detaylı şema bulunamadı).

**Response** `VoteReviewResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| reviewId | `Guid` | Review id |
| helpfulCount | `int` | Helpful count |
| notHelpfulCount | `int` | Not helpful count |
| message | `string` | Message |
Örnek Yanıt:
```json
{
  "reviewId": "11111111-1111-1111-1111-111111111111",
  "helpfulCount": 0,
  "notHelpfulCount": 0,
  "message": "string"
}
```
---

#### GET `/api/templates/available`
Controller `TemplatesController` • Action `GetAvailableTemplates`
Get available templates.

**Response** `GetAvailableTemplatesResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| templates | `List<TemplateDto>` | Templates |
Örnek Yanıt:
```json
{
  "templates": [
    {}
  ]
}
```
---

#### POST `/api/templates/select`
Controller `TemplatesController` • Action `SelectTemplate`
Select template.

Request body `SelectTemplateCommand` (detaylı şema bulunamadı).

**Response** `SelectTemplateResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| tenantId | `Guid` | Tenant id |
| templateCode | `string` | Template code |
| templateVersion | `int` | Template version |
| message | `string` | Message |
| setupStarted | `bool` | Setup started |
Örnek Yanıt:
```json
{
  "tenantId": "11111111-1111-1111-1111-111111111111",
  "templateCode": "string",
  "templateVersion": 0,
  "message": "string",
  "setupStarted": true
}
```
---

#### GET `/api/templates/selected`
Controller `TemplatesController` • Action `GetSelectedTemplate`
Get selected template.

**Response** `GetSelectedTemplateResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| templateCode | `string?` | Template code |
| templateVersion | `int?` | Template version |
| selectedAt | `DateTime?` | Selected at |
Örnek Yanıt:
```json
{
  "templateCode": "string",
  "templateVersion": 0,
  "selectedAt": "2024-01-01T00:00:00Z"
}
```
---

#### GET `/api/tenant/layout`
Controller `TenantController` • Action `GetLayoutSettings`
Get layout settings.

**Response** `GetLayoutSettingsResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| tenantId | `Guid` | Tenant id |
| layoutSettings | `Dictionary<string, object>?` | Layout settings |
Örnek Yanıt:
```json
{
  "tenantId": "11111111-1111-1111-1111-111111111111",
  "layoutSettings": {
    "key": "value"
  }
}
```
---

#### PUT `/api/tenant/layout`
Controller `TenantController` • Action `UpdateLayoutSettings`
Update layout settings.

Request body `UpdateLayoutSettingsCommand` (detaylı şema bulunamadı).

**Response** `UpdateLayoutSettingsResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| tenantId | `Guid` | Tenant id |
| layoutSettings | `Dictionary<string, object>` | Layout settings |
| message | `string` | Message |
Örnek Yanıt:
```json
{
  "tenantId": "11111111-1111-1111-1111-111111111111",
  "layoutSettings": {
    "key": "value"
  },
  "message": "string"
}
```
---

#### GET `/api/tenant/public`
Controller `TenantController` • Action `GetPublicInfo`
Get public info.

**Query Parametreleri**
| Ad | Tip | Açıklama |
| --- | --- | --- |
| slug | `string?` | Slug |

**Response** `GetTenantPublicInfoResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| tenantId | `Guid` | Tenant id |
| name | `string` | Name |
| facebookUrl | `string?` | Facebook url |
| instagramUrl | `string?` | Instagram url |
| twitterUrl | `string?` | Twitter url |
| linkedInUrl | `string?` | Linked in url |
| youTubeUrl | `string?` | You tube url |
| tikTokUrl | `string?` | Tik tok url |
| pinterestUrl | `string?` | Pinterest url |
| whatsAppNumber | `string?` | Whats app number |
| telegramUsername | `string?` | Telegram username |
| email | `string?` | Email |
| phone | `string?` | Phone |
| address | `string?` | Address |
| city | `string?` | City |
| country | `string?` | Country |
| logoUrl | `string?` | Logo url |
| faviconUrl | `string?` | Favicon url |
| siteTitle | `string?` | Site title |
| siteDescription | `string?` | Site description |
| primaryColor | `string?` | Primary color |
| secondaryColor | `string?` | Secondary color |
| backgroundColor | `string?` | Background color |
| textColor | `string?` | Text color |
| linkColor | `string?` | Link color |
| buttonColor | `string?` | Button color |
| buttonTextColor | `string?` | Button text color |
| fontFamily | `string?` | Font family |
| headingFontFamily | `string?` | Heading font family |
| baseFontSize | `int?` | Base font size |
| layoutSettings | `Dictionary<string, object>?` | Layout settings |
Örnek Yanıt:
```json
{
  "tenantId": "11111111-1111-1111-1111-111111111111",
  "name": "string",
  "facebookUrl": "string",
  "instagramUrl": "string",
  "twitterUrl": "string",
  "linkedInUrl": "string",
  "youTubeUrl": "string",
  "tikTokUrl": "string",
  "pinterestUrl": "string",
  "whatsAppNumber": "string",
  "telegramUsername": "string",
  "email": "string",
  "phone": "string",
  "address": "string",
  "city": "string",
  "country": "string",
  "logoUrl": "string",
  "faviconUrl": "string",
  "siteTitle": "string",
  "siteDescription": "string",
  "primaryColor": "string",
  "secondaryColor": "string",
  "backgroundColor": "string",
  "textColor": "string",
  "linkColor": "string",
  "buttonColor": "string",
  "buttonTextColor": "string",
  "fontFamily": "string",
  "headingFontFamily": "string",
  "baseFontSize": 0,
  "layoutSettings": {
    "key": "value"
  }
}
```
---

#### GET `/api/tenant/settings`
Controller `TenantController` • Action `GetSettings`
Get settings.

**Response** `GetTenantSettingsResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| tenantId | `Guid` | Tenant id |
| name | `string` | Name |
| slug | `string` | Slug |
| facebookUrl | `string?` | Facebook url |
| instagramUrl | `string?` | Instagram url |
| twitterUrl | `string?` | Twitter url |
| linkedInUrl | `string?` | Linked in url |
| youTubeUrl | `string?` | You tube url |
| tikTokUrl | `string?` | Tik tok url |
| pinterestUrl | `string?` | Pinterest url |
| whatsAppNumber | `string?` | Whats app number |
| telegramUsername | `string?` | Telegram username |
| email | `string?` | Email |
| phone | `string?` | Phone |
| address | `string?` | Address |
| city | `string?` | City |
| country | `string?` | Country |
| logoUrl | `string?` | Logo url |
| faviconUrl | `string?` | Favicon url |
| siteTitle | `string?` | Site title |
| siteDescription | `string?` | Site description |
| primaryColor | `string?` | Primary color |
| secondaryColor | `string?` | Secondary color |
| backgroundColor | `string?` | Background color |
| textColor | `string?` | Text color |
| linkColor | `string?` | Link color |
| buttonColor | `string?` | Button color |
| buttonTextColor | `string?` | Button text color |
| fontFamily | `string?` | Font family |
| headingFontFamily | `string?` | Heading font family |
| baseFontSize | `int?` | Base font size |
Örnek Yanıt:
```json
{
  "tenantId": "11111111-1111-1111-1111-111111111111",
  "name": "string",
  "slug": "string",
  "facebookUrl": "string",
  "instagramUrl": "string",
  "twitterUrl": "string",
  "linkedInUrl": "string",
  "youTubeUrl": "string",
  "tikTokUrl": "string",
  "pinterestUrl": "string",
  "whatsAppNumber": "string",
  "telegramUsername": "string",
  "email": "string",
  "phone": "string",
  "address": "string",
  "city": "string",
  "country": "string",
  "logoUrl": "string",
  "faviconUrl": "string",
  "siteTitle": "string",
  "siteDescription": "string",
  "primaryColor": "string",
  "secondaryColor": "string",
  "backgroundColor": "string",
  "textColor": "string",
  "linkColor": "string",
  "buttonColor": "string",
  "buttonTextColor": "string",
  "fontFamily": "string",
  "headingFontFamily": "string",
  "baseFontSize": 0
}
```
---

#### PUT `/api/tenant/settings`
Controller `TenantController` • Action `UpdateSettings`
Update settings.

Request body `UpdateTenantSettingsCommand` (detaylı şema bulunamadı).

**Response** `UpdateTenantSettingsResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| tenantId | `Guid` | Tenant id |
| name | `string` | Name |
| message | `string` | Message |
Örnek Yanıt:
```json
{
  "tenantId": "11111111-1111-1111-1111-111111111111",
  "name": "string",
  "message": "string"
}
```
---

### Tinisoft.Customers.API
Storefront customer auth, profile, cart and checkout.

#### GET `/api/customers/addresses`
Controller `CustomersController` • Action `GetAddresses`
Get addresses.

**Response** `List<CustomerAddressDto>`
Dönen veri `List<CustomerAddressDto>` tipinde liste.
```json
[
  {
    "addressId": "11111111-1111-1111-1111-111111111111",
    "addressLine1": "string",
    "addressLine2": "string",
    "city": "string",
    "state": "string",
    "postalCode": "string",
    "country": "string",
    "phone": "string",
    "addressTitle": "string",
    "isDefaultShipping": true,
    "isDefaultBilling": true
  }
]
```
---

#### POST `/api/customers/addresses`
Controller `CustomersController` • Action `AddAddress`
Add address.

Request body `AddCustomerAddressCommand` (detaylı şema bulunamadı).

**Response** `CustomerAddressDto`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| addressId | `Guid` | Address id |
| addressLine1 | `string` | Address line1 |
| addressLine2 | `string?` | Address line2 |
| city | `string` | City |
| state | `string?` | State |
| postalCode | `string` | Postal code |
| country | `string` | Country |
| phone | `string?` | Phone |
| addressTitle | `string?` | Address title |
| isDefaultShipping | `bool` | Is default shipping |
| isDefaultBilling | `bool` | Is default billing |
Örnek Yanıt:
```json
{
  "addressId": "11111111-1111-1111-1111-111111111111",
  "addressLine1": "string",
  "addressLine2": "string",
  "city": "string",
  "state": "string",
  "postalCode": "string",
  "country": "string",
  "phone": "string",
  "addressTitle": "string",
  "isDefaultShipping": true,
  "isDefaultBilling": true
}
```
---

#### DELETE `/api/customers/cart`
Controller `CustomersController` • Action `ClearCart`
Clear cart.

**Response** `ClearCartResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| success | `bool` | Success |
Örnek Yanıt:
```json
{
  "success": true
}
```
---

#### GET `/api/customers/cart`
Controller `CustomersController` • Action `GetCart`
Get cart.

**Response** `GetCartResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| cartId | `Guid` | Cart id |
| items | `List<CartItemDto>` | Items |
| couponCode | `string?` | Coupon code |
| couponName | `string?` | Coupon name |
| subtotal | `decimal` | Subtotal |
| tax | `decimal` | Tax |
| shipping | `decimal` | Shipping |
| discount | `decimal` | Discount |
| total | `decimal` | Total |
| currency | `string` | Currency |
| lastUpdatedAt | `DateTime` | Last updated at |
Örnek Yanıt:
```json
{
  "cartId": "11111111-1111-1111-1111-111111111111",
  "items": [
    {}
  ],
  "couponCode": "string",
  "couponName": "string",
  "subtotal": 0,
  "tax": 0,
  "shipping": 0,
  "discount": 0,
  "total": 0,
  "currency": "string",
  "lastUpdatedAt": "2024-01-01T00:00:00Z"
}
```
---

#### POST `/api/customers/cart/apply-coupon`
Controller `CustomersController` • Action `ApplyCouponToCart`
Apply coupon to cart.

Request body `ApplyCouponToCartCommand` (detaylı şema bulunamadı).

**Response** `ApplyCouponToCartResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| success | `bool` | Success |
| errorMessage | `string?` | Error message |
| couponCode | `string?` | Coupon code |
| couponName | `string?` | Coupon name |
| discountAmount | `decimal` | Discount amount |
| cartTotal | `decimal` | Cart total |
Örnek Yanıt:
```json
{
  "success": true,
  "errorMessage": "string",
  "couponCode": "string",
  "couponName": "string",
  "discountAmount": 0,
  "cartTotal": 0
}
```
---

#### DELETE `/api/customers/cart/coupon`
Controller `CustomersController` • Action `RemoveCouponFromCart`
Remove coupon from cart.

**Response** `RemoveCouponFromCartResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| success | `bool` | Success |
| cartTotal | `decimal` | Cart total |
Örnek Yanıt:
```json
{
  "success": true,
  "cartTotal": 0
}
```
---

#### POST `/api/customers/cart/items`
Controller `CustomersController` • Action `AddCartItem`
Add cart item.

Request body `AddCartItemCommand` (detaylı şema bulunamadı).

**Response** `AddCartItemResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| cartItemId | `Guid` | Cart item id |
| cartId | `Guid` | Cart id |
| item | `CartItemDto` | Item |
| cartTotal | `decimal` | Cart total |
Örnek Yanıt:
```json
{
  "cartItemId": "11111111-1111-1111-1111-111111111111",
  "cartId": "11111111-1111-1111-1111-111111111111",
  "item": {
    "id": "11111111-1111-1111-1111-111111111111",
    "productId": "11111111-1111-1111-1111-111111111111",
    "productVariantId": "11111111-1111-1111-1111-111111111111",
    "title": "string",
    "sKU": "string",
    "quantity": 0,
    "unitPrice": 0,
    "totalPrice": 0,
    "currency": "string"
  },
  "cartTotal": 0
}
```
---

#### DELETE `/api/customers/cart/items/{id}`
Controller `CustomersController` • Action `RemoveCartItem`
Remove cart item.

**Path Parametreleri**
| Ad | Tip | Açıklama |
| --- | --- | --- |
| id | `Guid` | Id |

**Response** `RemoveCartItemResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| success | `bool` | Success |
| cartTotal | `decimal` | Cart total |
Örnek Yanıt:
```json
{
  "success": true,
  "cartTotal": 0
}
```
---

#### PUT `/api/customers/cart/items/{id}`
Controller `CustomersController` • Action `UpdateCartItem`
Update cart item.

**Path Parametreleri**
| Ad | Tip | Açıklama |
| --- | --- | --- |
| id | `Guid` | Id |

Request body `UpdateCartItemCommand` (detaylı şema bulunamadı).

**Response** `UpdateCartItemResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| cartItemId | `Guid` | Cart item id |
| item | `CartItemDto` | Item |
| cartTotal | `decimal` | Cart total |
Örnek Yanıt:
```json
{
  "cartItemId": "11111111-1111-1111-1111-111111111111",
  "item": {
    "id": "11111111-1111-1111-1111-111111111111",
    "productId": "11111111-1111-1111-1111-111111111111",
    "productVariantId": "11111111-1111-1111-1111-111111111111",
    "title": "string",
    "sKU": "string",
    "quantity": 0,
    "unitPrice": 0,
    "totalPrice": 0,
    "currency": "string"
  },
  "cartTotal": 0
}
```
---

#### POST `/api/customers/login`
Controller `CustomersController` • Action `Login`
Login.

Request body `LoginCustomerCommand` (detaylı şema bulunamadı).

**Response** `CustomerLoginResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| customerId | `Guid` | Customer id |
| email | `string` | Email |
| firstName | `string?` | First name |
| lastName | `string?` | Last name |
| phone | `string?` | Phone |
| token | `string` | Token |
Örnek Yanıt:
```json
{
  "customerId": "11111111-1111-1111-1111-111111111111",
  "email": "string",
  "firstName": "string",
  "lastName": "string",
  "phone": "string",
  "token": "string"
}
```
---

#### GET `/api/customers/orders`
Controller `CustomersController` • Action `GetOrders`
Get orders.

**Query Parametreleri**
| Ad | Tip | Açıklama |
| --- | --- | --- |
| query | `GetCustomerOrdersQuery` | Query |

**Response** `GetCustomerOrdersResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| orders | `List<CustomerOrderDto>` | Orders |
| totalCount | `int` | Total count |
| page | `int` | Page |
| pageSize | `int` | Page size |
Örnek Yanıt:
```json
{
  "orders": [
    {}
  ],
  "totalCount": 0,
  "page": 0,
  "pageSize": 0
}
```
---

#### POST `/api/customers/orders/checkout`
Controller `CustomersController` • Action `CheckoutFromCart`
Checkout from cart.

Request body `CheckoutFromCartCommand` (detaylı şema bulunamadı).

**Response** `CheckoutFromCartResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| orderId | `Guid` | Order id |
| orderNumber | `string` | Order number |
| total | `decimal` | Total |
| status | `string` | Status |
| paymentUrl | `string?` | Payment url |
Örnek Yanıt:
```json
{
  "orderId": "11111111-1111-1111-1111-111111111111",
  "orderNumber": "string",
  "total": 0,
  "status": "string",
  "paymentUrl": "string"
}
```
---

#### GET `/api/customers/orders/{id}`
Controller `CustomersController` • Action `GetOrder`
Get order.

**Path Parametreleri**
| Ad | Tip | Açıklama |
| --- | --- | --- |
| id | `Guid` | Id |

**Response** `GetCustomerOrderResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| id | `Guid` | Id |
| orderNumber | `string` | Order number |
| status | `string` | Status |
| customerEmail | `string` | Customer email |
| customerPhone | `string?` | Customer phone |
| customerFirstName | `string?` | Customer first name |
| customerLastName | `string?` | Customer last name |
| shippingAddress | `ShippingAddressDto` | Shipping address |
| totals | `OrderTotalsDto` | Totals |
| paymentStatus | `string?` | Payment status |
| paymentProvider | `string?` | Payment provider |
| paidAt | `DateTime?` | Paid at |
| shippingMethod | `string?` | Shipping method |
| trackingNumber | `string?` | Tracking number |
| items | `List<OrderItemDto>` | Items |
| createdAt | `DateTime` | Created at |
| updatedAt | `DateTime?` | Updated at |
Örnek Yanıt:
```json
{
  "id": "11111111-1111-1111-1111-111111111111",
  "orderNumber": "string",
  "status": "string",
  "customerEmail": "string",
  "customerPhone": "string",
  "customerFirstName": "string",
  "customerLastName": "string",
  "shippingAddress": {
    "addressLine1": "string",
    "addressLine2": "string",
    "city": "string",
    "state": "string",
    "postalCode": "string",
    "country": "string"
  },
  "totals": {
    "subtotal": 0,
    "tax": 0,
    "shipping": 0,
    "discount": 0,
    "total": 0
  },
  "paymentStatus": "string",
  "paymentProvider": "string",
  "paidAt": "2024-01-01T00:00:00Z",
  "shippingMethod": "string",
  "trackingNumber": "string",
  "items": [
    {}
  ],
  "createdAt": "2024-01-01T00:00:00Z",
  "updatedAt": "2024-01-01T00:00:00Z"
}
```
---

#### GET `/api/customers/profile`
Controller `CustomersController` • Action `GetProfile`
Get profile.

**Response** `CustomerDto`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| id | `Guid` | Id |
| email | `string` | Email |
| firstName | `string?` | First name |
| lastName | `string?` | Last name |
| phone | `string?` | Phone |
| emailVerified | `bool` | Email verified |
| createdAt | `DateTime` | Created at |
Örnek Yanıt:
```json
{
  "id": "11111111-1111-1111-1111-111111111111",
  "email": "string",
  "firstName": "string",
  "lastName": "string",
  "phone": "string",
  "emailVerified": true,
  "createdAt": "2024-01-01T00:00:00Z"
}
```
---

#### PUT `/api/customers/profile`
Controller `CustomersController` • Action `UpdateProfile`
Update profile.

Request body `UpdateCustomerProfileCommand` (detaylı şema bulunamadı).

**Response** `CustomerDto`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| id | `Guid` | Id |
| email | `string` | Email |
| firstName | `string?` | First name |
| lastName | `string?` | Last name |
| phone | `string?` | Phone |
| emailVerified | `bool` | Email verified |
| createdAt | `DateTime` | Created at |
Örnek Yanıt:
```json
{
  "id": "11111111-1111-1111-1111-111111111111",
  "email": "string",
  "firstName": "string",
  "lastName": "string",
  "phone": "string",
  "emailVerified": true,
  "createdAt": "2024-01-01T00:00:00Z"
}
```
---

#### POST `/api/customers/register`
Controller `CustomersController` • Action `Register`
Register.

Request body `RegisterCustomerCommand` (detaylı şema bulunamadı).

**Response** `CustomerAuthResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| customerId | `Guid` | Customer id |
| email | `string` | Email |
| firstName | `string?` | First name |
| lastName | `string?` | Last name |
| phone | `string?` | Phone |
| token | `string` | Token |
Örnek Yanıt:
```json
{
  "customerId": "11111111-1111-1111-1111-111111111111",
  "email": "string",
  "firstName": "string",
  "lastName": "string",
  "phone": "string",
  "token": "string"
}
```
---

### Tinisoft.Inventory.API
Warehouse stock ops exposed to internal jobs.

#### POST `/api/inventory/adjust`
Controller `InventoryController` • Action `AdjustStock`
Adjust stock.

Request body `AdjustStockCommand` (detaylı şema bulunamadı).

**Response** `AdjustStockResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| productId | `Guid` | Product id |
| variantId | `Guid?` | Variant id |
| oldQuantity | `int` | Old quantity |
| newQuantity | `int` | New quantity |
Örnek Yanıt:
```json
{
  "productId": "11111111-1111-1111-1111-111111111111",
  "variantId": "11111111-1111-1111-1111-111111111111",
  "oldQuantity": 0,
  "newQuantity": 0
}
```
---

#### GET `/api/inventory/products/{productId}`
Controller `InventoryController` • Action `GetStockLevel`
Get stock level.

**Path Parametreleri**
| Ad | Tip | Açıklama |
| --- | --- | --- |
| productId | `Guid` | Product id |

**Query Parametreleri**
| Ad | Tip | Açıklama |
| --- | --- | --- |
| variantId | `Guid?` | Variant id |

**Response** `GetStockLevelResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| productId | `Guid` | Product id |
| variantId | `Guid?` | Variant id |
| quantity | `int?` | Quantity |
| trackInventory | `bool` | Track inventory |
| isLowStock | `bool` | Is low stock |
Örnek Yanıt:
```json
{
  "productId": "11111111-1111-1111-1111-111111111111",
  "variantId": "11111111-1111-1111-1111-111111111111",
  "quantity": 0,
  "trackInventory": true,
  "isLowStock": true
}
```
---

### Tinisoft.Invoices.API
E-invoice issuing, GIB integration and settings.

#### GET `/api/invoices`
Controller `InvoicesController` • Action `GetInvoices`
Get invoices.

**Query Parametreleri**
| Ad | Tip | Açıklama |
| --- | --- | --- |
| query | `GetInvoicesQuery` | Query |

**Response** `GetInvoicesResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| invoices | `List<InvoiceListItemDto>` | Invoices |
| totalCount | `int` | Total count |
| page | `int` | Page |
| pageSize | `int` | Page size |
Örnek Yanıt:
```json
{
  "invoices": [
    {}
  ],
  "totalCount": 0,
  "page": 0,
  "pageSize": 0
}
```
---

#### POST `/api/invoices`
Controller `InvoicesController` • Action `CreateInvoice`
Create invoice.

Request body `CreateInvoiceCommand` (detaylı şema bulunamadı).

**Response** `CreateInvoiceResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| invoiceId | `Guid` | Invoice id |
| invoiceNumber | `string` | Invoice number |
| invoiceSerial | `string` | Invoice serial |
| status | `string` | Status |
| gIBInvoiceId | `string?` | G i b invoice id |
| pDFUrl | `string?` | P d f url |
| message | `string` | Message |
Örnek Yanıt:
```json
{
  "invoiceId": "11111111-1111-1111-1111-111111111111",
  "invoiceNumber": "string",
  "invoiceSerial": "string",
  "status": "string",
  "gIBInvoiceId": "string",
  "pDFUrl": "string",
  "message": "string"
}
```
---

#### GET `/api/invoices/inbox`
Controller `InvoicesController` • Action `GetInboxInvoices`
Get inbox invoices.

**Query Parametreleri**
| Ad | Tip | Açıklama |
| --- | --- | --- |
| startDate | `DateTime?` | Start date |
| endDate | `DateTime?` | End date |
| senderVKN | `string?` | Sender v k n |

**Response** `GetInboxInvoicesResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| invoices | `List<InboxInvoiceDto>` | Invoices |
| totalCount | `int` | Total count |
Örnek Yanıt:
```json
{
  "invoices": [
    {}
  ],
  "totalCount": 0
}
```
---

#### GET `/api/invoices/settings`
Controller `InvoicesController` • Action `GetInvoiceSettings`
Get invoice settings.

**Response** `GetInvoiceSettingsResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| tenantId | `Guid` | Tenant id |
| isEFaturaUser | `bool` | Is e fatura user |
| vKN | `string?` | V k n |
| tCKN | `string?` | T c k n |
| taxOffice | `string?` | Tax office |
| taxNumber | `string?` | Tax number |
| eFaturaAlias | `string?` | E fatura alias |
| companyName | `string?` | Company name |
| companyTitle | `string?` | Company title |
| companyAddressLine1 | `string?` | Company address line1 |
| companyAddressLine2 | `string?` | Company address line2 |
| companyCity | `string?` | Company city |
| companyState | `string?` | Company state |
| companyPostalCode | `string?` | Company postal code |
| companyCountry | `string?` | Company country |
| companyPhone | `string?` | Company phone |
| companyEmail | `string?` | Company email |
| companyWebsite | `string?` | Company website |
| bankName | `string?` | Bank name |
| bankBranch | `string?` | Bank branch |
| iBAN | `string?` | I b a n |
| accountName | `string?` | Account name |
| maliMuhurSerialNumber | `string?` | Mali muhur serial number |
| maliMuhurExpiryDate | `DateTime?` | Mali muhur expiry date |
| hasMaliMuhur | `bool` | Has mali muhur |
| invoicePrefix | `string` | Invoice prefix |
| invoiceSerial | `string` | Invoice serial |
| invoiceStartNumber | `int` | Invoice start number |
| lastInvoiceNumber | `int` | Last invoice number |
| defaultInvoiceType | `string` | Default invoice type |
| defaultProfileId | `string` | Default profile id |
| paymentDueDays | `int` | Payment due days |
| autoCreateInvoiceOnOrderPaid | `bool` | Auto create invoice on order paid |
| autoSendToGIB | `bool` | Auto send to g i b |
| useTestEnvironment | `bool` | Use test environment |
| isActive | `bool` | Is active |
Örnek Yanıt:
```json
{
  "tenantId": "11111111-1111-1111-1111-111111111111",
  "isEFaturaUser": true,
  "vKN": "string",
  "tCKN": "string",
  "taxOffice": "string",
  "taxNumber": "string",
  "eFaturaAlias": "string",
  "companyName": "string",
  "companyTitle": "string",
  "companyAddressLine1": "string",
  "companyAddressLine2": "string",
  "companyCity": "string",
  "companyState": "string",
  "companyPostalCode": "string",
  "companyCountry": "string",
  "companyPhone": "string",
  "companyEmail": "string",
  "companyWebsite": "string",
  "bankName": "string",
  "bankBranch": "string",
  "iBAN": "string",
  "accountName": "string",
  "maliMuhurSerialNumber": "string",
  "maliMuhurExpiryDate": "2024-01-01T00:00:00Z",
  "hasMaliMuhur": true,
  "invoicePrefix": "string",
  "invoiceSerial": "string",
  "invoiceStartNumber": 0,
  "lastInvoiceNumber": 0,
  "defaultInvoiceType": "string",
  "defaultProfileId": "string",
  "paymentDueDays": 0,
  "autoCreateInvoiceOnOrderPaid": true,
  "autoSendToGIB": true,
  "useTestEnvironment": true,
  "isActive": true
}
```
---

#### PUT `/api/invoices/settings`
Controller `InvoicesController` • Action `UpdateInvoiceSettings`
Update invoice settings.

Request body `UpdateInvoiceSettingsCommand` (detaylı şema bulunamadı).

**Response** `UpdateInvoiceSettingsResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| tenantId | `Guid` | Tenant id |
| isEFaturaUser | `bool` | Is e fatura user |
| vKN | `string?` | V k n |
| message | `string` | Message |
Örnek Yanıt:
```json
{
  "tenantId": "11111111-1111-1111-1111-111111111111",
  "isEFaturaUser": true,
  "vKN": "string",
  "message": "string"
}
```
---

#### GET `/api/invoices/{id}`
Controller `InvoicesController` • Action `GetInvoice`
Get invoice.

**Path Parametreleri**
| Ad | Tip | Açıklama |
| --- | --- | --- |
| id | `Guid` | Id |

**Query Parametreleri**
| Ad | Tip | Açıklama |
| --- | --- | --- |
| includePdf | `bool` | Include pdf |

**Response** `GetInvoiceResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| invoiceId | `Guid` | Invoice id |
| invoiceNumber | `string` | Invoice number |
| invoiceSerial | `string` | Invoice serial |
| invoiceDate | `DateTime` | Invoice date |
| invoiceType | `string` | Invoice type |
| profileId | `string` | Profile id |
| status | `string` | Status |
| statusMessage | `string?` | Status message |
| orderId | `Guid` | Order id |
| orderNumber | `string` | Order number |
| customerName | `string` | Customer name |
| customerEmail | `string?` | Customer email |
| customerVKN | `string?` | Customer v k n |
| subtotal | `decimal` | Subtotal |
| taxAmount | `decimal` | Tax amount |
| discountAmount | `decimal` | Discount amount |
| shippingAmount | `decimal` | Shipping amount |
| total | `decimal` | Total |
| currency | `string` | Currency |
| gIBInvoiceId | `string?` | G i b invoice id |
| gIBInvoiceNumber | `string?` | G i b invoice number |
| gIBSentAt | `DateTime?` | G i b sent at |
| gIBApprovedAt | `DateTime?` | G i b approved at |
| gIBApprovalStatus | `string?` | G i b approval status |
| pDFUrl | `string?` | P d f url |
| pDFGeneratedAt | `DateTime?` | P d f generated at |
| items | `List<InvoiceItemResponse>` | Items |
| createdAt | `DateTime` | Created at |
| updatedAt | `DateTime` | Updated at |
Örnek Yanıt:
```json
{
  "invoiceId": "11111111-1111-1111-1111-111111111111",
  "invoiceNumber": "string",
  "invoiceSerial": "string",
  "invoiceDate": "2024-01-01T00:00:00Z",
  "invoiceType": "string",
  "profileId": "string",
  "status": "string",
  "statusMessage": "string",
  "orderId": "11111111-1111-1111-1111-111111111111",
  "orderNumber": "string",
  "customerName": "string",
  "customerEmail": "string",
  "customerVKN": "string",
  "subtotal": 0,
  "taxAmount": 0,
  "discountAmount": 0,
  "shippingAmount": 0,
  "total": 0,
  "currency": "string",
  "gIBInvoiceId": "string",
  "gIBInvoiceNumber": "string",
  "gIBSentAt": "2024-01-01T00:00:00Z",
  "gIBApprovedAt": "2024-01-01T00:00:00Z",
  "gIBApprovalStatus": "string",
  "pDFUrl": "string",
  "pDFGeneratedAt": "2024-01-01T00:00:00Z",
  "items": [
    {}
  ],
  "createdAt": "2024-01-01T00:00:00Z",
  "updatedAt": "2024-01-01T00:00:00Z"
}
```
---

#### POST `/api/invoices/{id}/cancel`
Controller `InvoicesController` • Action `CancelInvoice`
Cancel invoice.

**Path Parametreleri**
| Ad | Tip | Açıklama |
| --- | --- | --- |
| id | `Guid` | Id |

Request body `CancelInvoiceCommand` (detaylı şema bulunamadı).

**Response** `CancelInvoiceResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| invoiceId | `Guid` | Invoice id |
| invoiceNumber | `string` | Invoice number |
| status | `string` | Status |
| cancellationInvoiceNumber | `string?` | Cancellation invoice number |
| message | `string` | Message |
Örnek Yanıt:
```json
{
  "invoiceId": "11111111-1111-1111-1111-111111111111",
  "invoiceNumber": "string",
  "status": "string",
  "cancellationInvoiceNumber": "string",
  "message": "string"
}
```
---

#### GET `/api/invoices/{id}/gib-status`
Controller `InvoicesController` • Action `GetInvoiceStatusFromGIB`
Get invoice status from g i b.

**Path Parametreleri**
| Ad | Tip | Açıklama |
| --- | --- | --- |
| id | `Guid` | Id |

**Response** `GetInvoiceStatusFromGIBResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| invoiceId | `Guid` | Invoice id |
| invoiceNumber | `string` | Invoice number |
| success | `bool` | Success |
| status | `string` | Status |
| statusMessage | `string?` | Status message |
| processedAt | `DateTime?` | Processed at |
| gIBInvoiceId | `string?` | G i b invoice id |
Örnek Yanıt:
```json
{
  "invoiceId": "11111111-1111-1111-1111-111111111111",
  "invoiceNumber": "string",
  "success": true,
  "status": "string",
  "statusMessage": "string",
  "processedAt": "2024-01-01T00:00:00Z",
  "gIBInvoiceId": "string"
}
```
---

#### POST `/api/invoices/{id}/send-to-gib`
Controller `InvoicesController` • Action `SendInvoiceToGIB`
Send invoice to g i b.

**Path Parametreleri**
| Ad | Tip | Açıklama |
| --- | --- | --- |
| id | `Guid` | Id |

**Response** `SendInvoiceToGIBResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| invoiceId | `Guid` | Invoice id |
| invoiceNumber | `string` | Invoice number |
| success | `bool` | Success |
| gIBInvoiceId | `string?` | G i b invoice id |
| gIBInvoiceNumber | `string?` | G i b invoice number |
| errorMessage | `string?` | Error message |
| message | `string` | Message |
Örnek Yanıt:
```json
{
  "invoiceId": "11111111-1111-1111-1111-111111111111",
  "invoiceNumber": "string",
  "success": true,
  "gIBInvoiceId": "string",
  "gIBInvoiceNumber": "string",
  "errorMessage": "string",
  "message": "string"
}
```
---

### Tinisoft.Marketplace.API
Marketplace integrations (Trendyol, Hepsiburada, N11).

#### POST `/api/marketplace/sync/products`
Controller `MarketplaceController` • Action `SyncProducts`
Sync products.

Request body `SyncProductsCommand` (detaylı şema bulunamadı).

**Response** `SyncProductsResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| syncedCount | `int` | Synced count |
| failedCount | `int` | Failed count |
| errors | `List<string>` | Errors |
Örnek Yanıt:
```json
{
  "syncedCount": 0,
  "failedCount": 0,
  "errors": [
    "string"
  ]
}
```
---

### Tinisoft.Notifications.API
Transactional email providers/templates/send.

#### POST `/api/notifications/email-providers`
Controller `NotificationsController` • Action `CreateEmailProvider`
Create email provider.

Request body `CreateEmailProviderCommand` (detaylı şema bulunamadı).

**Response** `CreateEmailProviderResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| emailProviderId | `Guid` | Email provider id |
| providerName | `string` | Provider name |
Örnek Yanıt:
```json
{
  "emailProviderId": "11111111-1111-1111-1111-111111111111",
  "providerName": "string"
}
```
---

#### GET `/api/notifications/email-templates`
Controller `NotificationsController` • Action `GetEmailTemplates`
Get email templates.

**Query Parametreleri**
| Ad | Tip | Açıklama |
| --- | --- | --- |
| query | `GetEmailTemplatesQuery` | Query |

**Response** `GetEmailTemplatesResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| templates | `List<EmailTemplateDto>` | Templates |
Örnek Yanıt:
```json
{
  "templates": [
    {}
  ]
}
```
---

#### POST `/api/notifications/email-templates`
Controller `NotificationsController` • Action `CreateEmailTemplate`
Create email template.

Request body `CreateEmailTemplateCommand` (detaylı şema bulunamadı).

**Response** `CreateEmailTemplateResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| emailTemplateId | `Guid` | Email template id |
| templateCode | `string` | Template code |
| templateName | `string` | Template name |
Örnek Yanıt:
```json
{
  "emailTemplateId": "11111111-1111-1111-1111-111111111111",
  "templateCode": "string",
  "templateName": "string"
}
```
---

#### POST `/api/notifications/send-email`
Controller `NotificationsController` • Action `SendEmail`
Send email.

Request body `SendEmailCommand` (detaylı şema bulunamadı).

**Response** `SendEmailResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| emailNotificationId | `Guid` | Email notification id |
| success | `bool` | Success |
| errorMessage | `string?` | Error message |
Örnek Yanıt:
```json
{
  "emailNotificationId": "11111111-1111-1111-1111-111111111111",
  "success": true,
  "errorMessage": "string"
}
```
---

### Tinisoft.Orders.API
Order creation, retrieval and status updates.

#### POST `/api/orders`
Controller `OrdersController` • Action `CreateOrder`
Create order.

Request body `CreateOrderCommand` (detaylı şema bulunamadı).

**Response** `CreateOrderResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| orderId | `Guid` | Order id |
| orderNumber | `string` | Order number |
| total | `decimal` | Total |
Örnek Yanıt:
```json
{
  "orderId": "11111111-1111-1111-1111-111111111111",
  "orderNumber": "string",
  "total": 0
}
```
---

#### GET `/api/orders/{id}`
Controller `OrdersController` • Action `GetOrder`
Get order.

**Path Parametreleri**
| Ad | Tip | Açıklama |
| --- | --- | --- |
| id | `Guid` | Id |

**Response** `GetOrderResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| id | `Guid` | Id |
| orderNumber | `string` | Order number |
| status | `string` | Status |
| customerEmail | `string` | Customer email |
| customerPhone | `string?` | Customer phone |
| customerFirstName | `string?` | Customer first name |
| customerLastName | `string?` | Customer last name |
| totals | `OrderTotalsDto` | Totals |
| paymentStatus | `string?` | Payment status |
| paymentProvider | `string?` | Payment provider |
| paidAt | `DateTime?` | Paid at |
| shippingMethod | `string?` | Shipping method |
| trackingNumber | `string?` | Tracking number |
| createdAt | `DateTime` | Created at |
| items | `List<OrderItemResponse>` | Items |
Örnek Yanıt:
```json
{
  "id": "11111111-1111-1111-1111-111111111111",
  "orderNumber": "string",
  "status": "string",
  "customerEmail": "string",
  "customerPhone": "string",
  "customerFirstName": "string",
  "customerLastName": "string",
  "totals": {
    "subtotal": 0,
    "tax": 0,
    "shipping": 0,
    "discount": 0,
    "total": 0
  },
  "paymentStatus": "string",
  "paymentProvider": "string",
  "paidAt": "2024-01-01T00:00:00Z",
  "shippingMethod": "string",
  "trackingNumber": "string",
  "createdAt": "2024-01-01T00:00:00Z",
  "items": [
    {}
  ]
}
```
---

#### PUT `/api/orders/{id}/status`
Controller `OrdersController` • Action `UpdateOrderStatus`
Update order status.

**Path Parametreleri**
| Ad | Tip | Açıklama |
| --- | --- | --- |
| id | `Guid` | Id |

Request body `UpdateOrderStatusCommand` (detaylı şema bulunamadı).

**Response** `UpdateOrderStatusResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| orderId | `Guid` | Order id |
| status | `string` | Status |
Örnek Yanıt:
```json
{
  "orderId": "11111111-1111-1111-1111-111111111111",
  "status": "string"
}
```
---

### Tinisoft.Payments.API
Payment orchestration & PayTR callbacks.

#### POST `/api/payments/callback/paytr`
Controller `PaymentsController` • Action `PayTRCallback`
Pay t r callback.

**Form Parametreleri**
| Ad | Tip | Açıklama |
| --- | --- | --- |
| data | `Dictionary<string, string>` | Data |

**Response** `IActionResult`
İçerik custom `IActionResult` ile dönüyor.

---

#### POST `/api/payments/process`
Controller `PaymentsController` • Action `ProcessPayment`
Process payment.

Request body `ProcessPaymentCommand` (detaylı şema bulunamadı).

**Response** `ProcessPaymentResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| success | `bool` | Success |
| paymentToken | `string?` | Payment token |
| paymentReference | `string?` | Payment reference |
| errorMessage | `string?` | Error message |
| redirectUrl | `string?` | Redirect url |
Örnek Yanıt:
```json
{
  "success": true,
  "paymentToken": "string",
  "paymentReference": "string",
  "errorMessage": "string",
  "redirectUrl": "string"
}
```
---

#### POST `/api/payments/verify`
Controller `PaymentsController` • Action `VerifyPayment`
Verify payment.

Request body `VerifyPaymentCommand` (detaylı şema bulunamadı).

**Response** `VerifyPaymentResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| isValid | `bool` | Is valid |
| isPaid | `bool` | Is paid |
| errorMessage | `string?` | Error message |
Örnek Yanıt:
```json
{
  "isValid": true,
  "isPaid": true,
  "errorMessage": "string"
}
```
---

### Tinisoft.Products.API
Catalog management + storefront queries + tax.

#### GET `/api/products`
Controller `ProductsController` • Action `GetProducts`
Get products.

**Query Parametreleri**
| Ad | Tip | Açıklama |
| --- | --- | --- |
| query | `GetProductsQuery` | Query |

**Response** `GetProductsResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| items | `List<ProductListItemDto>` | Items |
| totalCount | `int` | Total count |
| page | `int` | Page |
| pageSize | `int` | Page size |
Örnek Yanıt:
```json
{
  "items": [
    {}
  ],
  "totalCount": 0,
  "page": 0,
  "pageSize": 0
}
```
---

#### POST `/api/products`
Controller `ProductsController` • Action `CreateProduct`
Create product.

Request body `CreateProductCommand` (detaylı şema bulunamadı).

**Response** `CreateProductResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| productId | `Guid` | Product id |
| title | `string` | Title |
Örnek Yanıt:
```json
{
  "productId": "11111111-1111-1111-1111-111111111111",
  "title": "string"
}
```
---

#### DELETE `/api/products/{id}`
Controller `ProductsController` • Action `DeleteProduct`
Delete product.

**Path Parametreleri**
| Ad | Tip | Açıklama |
| --- | --- | --- |
| id | `Guid` | Id |

**Response** `IActionResult`
İçerik custom `IActionResult` ile dönüyor.

---

#### GET `/api/products/{id}`
Controller `ProductsController` • Action `GetProduct`
Get product.

**Path Parametreleri**
| Ad | Tip | Açıklama |
| --- | --- | --- |
| id | `Guid` | Id |

**Response** `GetProductResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| id | `Guid` | Id |
| title | `string` | Title |
| description | `string?` | Description |
| shortDescription | `string?` | Short description |
| slug | `string` | Slug |
| sKU | `string?` | S k u |
| barcode | `string?` | Barcode |
| gTIN | `string?` | G t i n |
| price | `decimal` | Price |
| compareAtPrice | `decimal?` | Compare at price |
| costPerItem | `decimal` | Cost per item |
| currency | `string` | Currency |
| status | `string` | Status |
| trackInventory | `bool` | Track inventory |
| inventoryQuantity | `int?` | Inventory quantity |
| allowBackorder | `bool` | Allow backorder |
| weight | `decimal?` | Weight |
| weightUnit | `string?` | Weight unit |
| length | `decimal?` | Length |
| width | `decimal?` | Width |
| height | `decimal?` | Height |
| requiresShipping | `bool` | Requires shipping |
| isDigital | `bool` | Is digital |
| isTaxable | `bool` | Is taxable |
| taxCode | `string?` | Tax code |
| metaTitle | `string?` | Meta title |
| metaDescription | `string?` | Meta description |
| metaKeywords | `string?` | Meta keywords |
| vendor | `string?` | Vendor |
| productType | `string?` | Product type |
| publishedScope | `string` | Published scope |
| templateSuffix | `string?` | Template suffix |
| isGiftCard | `bool` | Is gift card |
| inventoryManagement | `string?` | Inventory management |
| fulfillmentService | `string?` | Fulfillment service |
| countryOfOrigin | `string?` | Country of origin |
| hSCode | `string?` | H s code |
| minQuantity | `int?` | Min quantity |
| maxQuantity | `int?` | Max quantity |
| incrementQuantity | `int?` | Increment quantity |
| shippingClass | `string?` | Shipping class |
| barcodeFormat | `string?` | Barcode format |
| unitPrice | `decimal?` | Unit price |
| unitPriceUnit | `string?` | Unit price unit |
| chargeTaxes | `bool` | Charge taxes |
| taxCategory | `string?` | Tax category |
| defaultInventoryLocationId | `Guid?` | Default inventory location id |
| isActive | `bool` | Is active |
| publishedAt | `DateTime?` | Published at |
| images | `List<ImageDto>` | Images |
| categories | `List<CategoryDto>` | Categories |
| variants | `List<VariantDto>` | Variants |
| options | `List<OptionDto>` | Options |
| metafields | `List<MetafieldDto>` | Metafields |
| tags | `List<string>` | Tags |
| collections | `List<string>` | Collections |
| salesChannels | `List<string>` | Sales channels |
| videoUrl | `string?` | Video url |
| videoThumbnailUrl | `string?` | Video thumbnail url |
| customFields | `Dictionary<string, object>?` | Custom fields |
| createdAt | `DateTime` | Created at |
| updatedAt | `DateTime?` | Updated at |
Örnek Yanıt:
```json
{
  "id": "11111111-1111-1111-1111-111111111111",
  "title": "string",
  "description": "string",
  "shortDescription": "string",
  "slug": "string",
  "sKU": "string",
  "barcode": "string",
  "gTIN": "string",
  "price": 0,
  "compareAtPrice": 0,
  "costPerItem": 0,
  "currency": "string",
  "status": "string",
  "trackInventory": true,
  "inventoryQuantity": 0,
  "allowBackorder": true,
  "weight": 0,
  "weightUnit": "string",
  "length": 0,
  "width": 0,
  "height": 0,
  "requiresShipping": true,
  "isDigital": true,
  "isTaxable": true,
  "taxCode": "string",
  "metaTitle": "string",
  "metaDescription": "string",
  "metaKeywords": "string",
  "vendor": "string",
  "productType": "string",
  "publishedScope": "string",
  "templateSuffix": "string",
  "isGiftCard": true,
  "inventoryManagement": "string",
  "fulfillmentService": "string",
  "countryOfOrigin": "string",
  "hSCode": "string",
  "minQuantity": 0,
  "maxQuantity": 0,
  "incrementQuantity": 0,
  "shippingClass": "string",
  "barcodeFormat": "string",
  "unitPrice": 0,
  "unitPriceUnit": "string",
  "chargeTaxes": true,
  "taxCategory": "string",
  "defaultInventoryLocationId": "11111111-1111-1111-1111-111111111111",
  "isActive": true,
  "publishedAt": "2024-01-01T00:00:00Z",
  "images": [
    {}
  ],
  "categories": [
    {}
  ],
  "variants": [
    {}
  ],
  "options": [
    {}
  ],
  "metafields": [
    {}
  ],
  "tags": [
    "string"
  ],
  "collections": [
    "string"
  ],
  "salesChannels": [
    "string"
  ],
  "videoUrl": "string",
  "videoThumbnailUrl": "string",
  "customFields": {
    "key": "value"
  },
  "createdAt": "2024-01-01T00:00:00Z",
  "updatedAt": "2024-01-01T00:00:00Z"
}
```
---

#### PUT `/api/products/{id}`
Controller `ProductsController` • Action `UpdateProduct`
Update product.

**Path Parametreleri**
| Ad | Tip | Açıklama |
| --- | --- | --- |
| id | `Guid` | Id |

Request body `UpdateProductCommand` (detaylı şema bulunamadı).

**Response** `UpdateProductResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| productId | `Guid` | Product id |
| title | `string` | Title |
Örnek Yanıt:
```json
{
  "productId": "11111111-1111-1111-1111-111111111111",
  "title": "string"
}
```
---

#### GET `/api/storefront/categories`
Controller `StorefrontController` • Action `GetCategories`
Get categories.

**Response** `GetStorefrontCategoriesResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| categories | `List<StorefrontCategoryDto>` | Categories |
Örnek Yanıt:
```json
{
  "categories": [
    {}
  ]
}
```
---

#### GET `/api/storefront/products`
Controller `StorefrontController` • Action `GetProducts`
Get products.

**Query Parametreleri**
| Ad | Tip | Açıklama |
| --- | --- | --- |
| query | `GetStorefrontProductsQuery` | Query |

**Response** `GetStorefrontProductsResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| items | `List<StorefrontProductDto>` | Items |
| totalCount | `int` | Total count |
| page | `int` | Page |
| pageSize | `int` | Page size |
| displayCurrency | `string` | Display currency |
Örnek Yanıt:
```json
{
  "items": [
    {}
  ],
  "totalCount": 0,
  "page": 0,
  "pageSize": 0,
  "displayCurrency": "string"
}
```
---

#### GET `/api/storefront/products/{id}`
Controller `StorefrontController` • Action `GetProduct`
Get product.

**Path Parametreleri**
| Ad | Tip | Açıklama |
| --- | --- | --- |
| id | `Guid` | Id |

**Query Parametreleri**
| Ad | Tip | Açıklama |
| --- | --- | --- |
| preferredCurrency | `string?` | Preferred currency |

**Response** `GetStorefrontProductResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| id | `Guid` | Id |
| title | `string` | Title |
| description | `string?` | Description |
| shortDescription | `string?` | Short description |
| slug | `string` | Slug |
| sKU | `string?` | S k u |
| price | `decimal` | Price |
| compareAtPrice | `decimal?` | Compare at price |
| currency | `string` | Currency |
| inventoryQuantity | `int?` | Inventory quantity |
| allowBackorder | `bool` | Allow backorder |
| weight | `decimal?` | Weight |
| weightUnit | `string?` | Weight unit |
| requiresShipping | `bool` | Requires shipping |
| isDigital | `bool` | Is digital |
| isTaxable | `bool` | Is taxable |
| metaTitle | `string?` | Meta title |
| metaDescription | `string?` | Meta description |
| metaKeywords | `string?` | Meta keywords |
| vendor | `string?` | Vendor |
| productType | `string?` | Product type |
| images | `List<StorefrontImageDto>` | Images |
| categories | `List<StorefrontCategoryDto>` | Categories |
| variants | `List<StorefrontVariantDto>` | Variants |
| options | `List<StorefrontOptionDto>` | Options |
| tags | `List<string>` | Tags |
| createdAt | `DateTime` | Created at |
Örnek Yanıt:
```json
{
  "id": "11111111-1111-1111-1111-111111111111",
  "title": "string",
  "description": "string",
  "shortDescription": "string",
  "slug": "string",
  "sKU": "string",
  "price": 0,
  "compareAtPrice": 0,
  "currency": "string",
  "inventoryQuantity": 0,
  "allowBackorder": true,
  "weight": 0,
  "weightUnit": "string",
  "requiresShipping": true,
  "isDigital": true,
  "isTaxable": true,
  "metaTitle": "string",
  "metaDescription": "string",
  "metaKeywords": "string",
  "vendor": "string",
  "productType": "string",
  "images": [
    {}
  ],
  "categories": [
    {}
  ],
  "variants": [
    {}
  ],
  "options": [
    {}
  ],
  "tags": [
    "string"
  ],
  "createdAt": "2024-01-01T00:00:00Z"
}
```
---

#### POST `/api/tax/calculate`
Controller `TaxController` • Action `CalculateTax`
Calculate tax.

Request body `CalculateTaxCommand` (detaylı şema bulunamadı).

**Response** `CalculateTaxResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| subtotal | `decimal` | Subtotal |
| taxAmount | `decimal` | Tax amount |
| total | `decimal` | Total |
| taxDetails | `List<TaxDetailDto>` | Tax details |
Örnek Yanıt:
```json
{
  "subtotal": 0,
  "taxAmount": 0,
  "total": 0,
  "taxDetails": [
    {}
  ]
}
```
---

#### GET `/api/tax/rates`
Controller `TaxController` • Action `GetTaxRates`
Get tax rates.

**Query Parametreleri**
| Ad | Tip | Açıklama |
| --- | --- | --- |
| isActive | `bool?` | Is active |

**Response** `List<TaxRateDto>`
Dönen veri `List<TaxRateDto>` tipinde liste.
```json
[
  {
    "id": "11111111-1111-1111-1111-111111111111",
    "name": "string",
    "code": "string",
    "rate": 0,
    "type": "string",
    "taxCode": "string",
    "exciseTaxCode": "string",
    "productServiceCode": "string",
    "isIncludedInPrice": true,
    "eInvoiceTaxType": "string",
    "isExempt": true,
    "exemptionReason": "string",
    "isActive": true,
    "description": "string"
  }
]
```
---

#### POST `/api/tax/rates`
Controller `TaxController` • Action `CreateTaxRate`
Create tax rate.

Request body `CreateTaxRateCommand` (detaylı şema bulunamadı).

**Response** `CreateTaxRateResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| taxRateId | `Guid` | Tax rate id |
| name | `string` | Name |
Örnek Yanıt:
```json
{
  "taxRateId": "11111111-1111-1111-1111-111111111111",
  "name": "string"
}
```
---

#### DELETE `/api/tax/rates/{id}`
Controller `TaxController` • Action `DeleteTaxRate`
Delete tax rate.

**Path Parametreleri**
| Ad | Tip | Açıklama |
| --- | --- | --- |
| id | `Guid` | Id |

**Response** `IActionResult`
İçerik custom `IActionResult` ile dönüyor.

---

#### PUT `/api/tax/rates/{id}`
Controller `TaxController` • Action `UpdateTaxRate`
Update tax rate.

**Path Parametreleri**
| Ad | Tip | Açıklama |
| --- | --- | --- |
| id | `Guid` | Id |

Request body `UpdateTaxRateCommand` (detaylı şema bulunamadı).

**Response** `UpdateTaxRateResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| taxRateId | `Guid` | Tax rate id |
| name | `string` | Name |
Örnek Yanıt:
```json
{
  "taxRateId": "11111111-1111-1111-1111-111111111111",
  "name": "string"
}
```
---

### Tinisoft.Shipping.API
Shipping providers, cost calculation, shipment creation.

#### POST `/api/shipping/calculate-cost`
Controller `ShippingController` • Action `CalculateShippingCost`
Calculate shipping cost.

Request body `CalculateShippingCostCommand` (detaylı şema bulunamadı).

**Response** `CalculateShippingCostResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| shippingCost | `decimal?` | Shipping cost |
| currency | `string` | Currency |
| providerCode | `string` | Provider code |
| providerName | `string` | Provider name |
| success | `bool` | Success |
| errorMessage | `string?` | Error message |
Örnek Yanıt:
```json
{
  "shippingCost": 0,
  "currency": "string",
  "providerCode": "string",
  "providerName": "string",
  "success": true,
  "errorMessage": "string"
}
```
---

#### GET `/api/shipping/providers`
Controller `ShippingController` • Action `GetShippingProviders`
Get shipping providers.

**Query Parametreleri**
| Ad | Tip | Açıklama |
| --- | --- | --- |
| query | `GetShippingProvidersQuery` | Query |

**Response** `GetShippingProvidersResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| providers | `List<ShippingProviderDto>` | Providers |
Örnek Yanıt:
```json
{
  "providers": [
    {}
  ]
}
```
---

#### POST `/api/shipping/providers`
Controller `ShippingController` • Action `CreateShippingProvider`
Create shipping provider.

Request body `CreateShippingProviderCommand` (detaylı şema bulunamadı).

**Response** `CreateShippingProviderResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| shippingProviderId | `Guid` | Shipping provider id |
| providerCode | `string` | Provider code |
| providerName | `string` | Provider name |
Örnek Yanıt:
```json
{
  "shippingProviderId": "11111111-1111-1111-1111-111111111111",
  "providerCode": "string",
  "providerName": "string"
}
```
---

#### PUT `/api/shipping/providers/{id}`
Controller `ShippingController` • Action `UpdateShippingProvider`
Update shipping provider.

**Path Parametreleri**
| Ad | Tip | Açıklama |
| --- | --- | --- |
| id | `Guid` | Id |

Request body `UpdateShippingProviderCommand` (detaylı şema bulunamadı).

**Response** `UpdateShippingProviderResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| shippingProviderId | `Guid` | Shipping provider id |
| providerCode | `string` | Provider code |
| providerName | `string` | Provider name |
Örnek Yanıt:
```json
{
  "shippingProviderId": "11111111-1111-1111-1111-111111111111",
  "providerCode": "string",
  "providerName": "string"
}
```
---

#### POST `/api/shipping/shipments`
Controller `ShippingController` • Action `CreateShipment`
Create shipment.

Request body `CreateShipmentCommand` (detaylı şema bulunamadı).

**Response** `CreateShipmentResponse`
| Alan | Tip | Açıklama |
| --- | --- | --- |
| trackingNumber | `string` | Tracking number |
| labelUrl | `string?` | Label url |
| shippingCost | `decimal` | Shipping cost |
| providerResponseJson | `string?` | Provider response json |
| success | `bool` | Success |
| errorMessage | `string?` | Error message |
Örnek Yanıt:
```json
{
  "trackingNumber": "string",
  "labelUrl": "string",
  "shippingCost": 0,
  "providerResponseJson": "string",
  "success": true,
  "errorMessage": "string"
}
```
---
