### Tinisoft.API (Core Tenant API)
Backoffice endpoints for tenants: auth, products, inventory, coupons, templates, etc.

#### Admin (/api/admin)
| Method | Path | Request | Response | Purpose |
| --- | --- | --- | --- | --- |
| GET | `/api/admin/statistics` | — | `GetSystemStatisticsResponse` | Get system statistics |

#### AdminTemplates (/api/admin/templates)
| Method | Path | Request | Response | Purpose |
| --- | --- | --- | --- | --- |
| GET | `/api/admin/templates` | — | `GetAllTemplatesResponse` | Get all templates |
| POST | `/api/admin/templates` | Body: CreateTemplateCommand command | `CreateTemplateResponse` | Create template |
| PUT | `/api/admin/templates/{id}` | Route: Guid id <br> Body: UpdateTemplateCommand command | `UpdateTemplateResponse` | Update template |
| DELETE | `/api/admin/templates/{id}` | Route: Guid id | `DeleteTemplateResponse` | Delete template |
| PATCH | `/api/admin/templates/{id}/toggle-active` | Route: Guid id <br> Body: ToggleTemplateActiveCommand command | `ToggleTemplateActiveResponse` | Toggle template active |

#### Auth (/api/auth)
| Method | Path | Request | Response | Purpose |
| --- | --- | --- | --- | --- |
| POST | `/api/auth/register` | Body: RegisterCommand command | `RegisterResponse` | Register |
| POST | `/api/auth/login` | Body: LoginCommand command | `LoginResponse` | Login |

#### Coupons (/api/coupons)
| Method | Path | Request | Response | Purpose |
| --- | --- | --- | --- | --- |
| GET | `/api/coupons` | Query: GetCouponsQuery query | `GetCouponsResponse` | Get coupons |
| POST | `/api/coupons` | Body: CreateCouponCommand command | `CreateCouponResponse` | Create coupon |
| PUT | `/api/coupons/{id}` | Route: Guid id <br> Body: UpdateCouponCommand command | `UpdateCouponResponse` | Update coupon |
| GET | `/api/coupons/{id}` | Route: Guid id | `GetCouponResponse` | Get coupon |
| GET | `/api/coupons/{id}/statistics` | Route: Guid id | `GetCouponStatisticsResponse` | Get coupon statistics |
| DELETE | `/api/coupons/{id}` | Route: Guid id | `DeleteCouponResponse` | Delete coupon |

#### Inventory (/api/inventory)
| Method | Path | Request | Response | Purpose |
| --- | --- | --- | --- | --- |
| GET | `/api/inventory/products/{productId}` | Route: Guid productId <br> Query: Guid? variantId | `GetStockLevelResponse` | Get stock level |
| POST | `/api/inventory/adjust` | Body: AdjustStockCommand command | `AdjustStockResponse` | Adjust stock |
| GET | `/api/inventory/orders/{orderId}/picking-list` | Route: Guid orderId | `GetPickingListResponse` | Get picking list |
| POST | `/api/inventory/pick` | Body: PickOrderItemCommand command | `PickOrderItemResponse` | Pick order item |
| POST | `/api/inventory/transfer` | Body: TransferStockCommand command | `TransferStockResponse` | Transfer stock |
| POST | `/api/inventory/locations` | Body: CreateWarehouseLocationCommand command | `CreateWarehouseLocationResponse` | Create warehouse location |
| GET | `/api/inventory/movements` | Query: GetStockMovementsQuery query | `GetStockMovementsResponse` | Get stock movements |
| GET | `/api/inventory/alerts/low-stock` | Query: GetLowStockAlertsQuery query | `GetLowStockAlertsResponse` | Get low stock alerts |
| POST | `/api/inventory/count` | Body: CountInventoryCommand command | `CountInventoryResponse` | Count inventory |
| GET | `/api/inventory/warehouse-stock` | Query: GetWarehouseStockQuery query | `GetWarehouseStockResponse` | Get warehouse stock |

#### Payments (/api/payments)
| Method | Path | Request | Response | Purpose |
| --- | --- | --- | --- | --- |
| POST | `/api/payments/process` | Body: ProcessPaymentCommand command | `ProcessPaymentResponse` | Process payment |
| POST | `/api/payments/verify` | Body: VerifyPaymentCommand command | `VerifyPaymentResponse` | Verify payment |
| POST | `/api/payments/callback/paytr` | Form: Dictionary<string, string> data | `IActionResult` | Pay t r callback |

#### Products (/api/products)
| Method | Path | Request | Response | Purpose |
| --- | --- | --- | --- | --- |
| GET | `/api/products` | Query: GetProductsQuery query | `GetProductsResponse` | Get products |
| GET | `/api/products/cursor` | Query: GetProductsCursorQuery query | `GetProductsCursorResponse` | Get products cursor |
| GET | `/api/products/{id}` | Route: Guid id | `GetProductResponse` | Get product |
| POST | `/api/products` | Body: CreateProductCommand command | `CreateProductResponse` | Create product |
| PUT | `/api/products/{id}` | Route: Guid id <br> Body: UpdateProductCommand command | `UpdateProductResponse` | Update product |
| DELETE | `/api/products/{id}` | Route: Guid id | `IActionResult` | Delete product |

#### Public (/api/public)
| Method | Path | Request | Response | Purpose |
| --- | --- | --- | --- | --- |
| GET | `/api/public/bootstrap` | — | `GetBootstrapDataResponse` | Bootstrap |

#### PublicFeeds (/api/public/feeds)
| Method | Path | Request | Response | Purpose |
| --- | --- | --- | --- | --- |
| GET | `/api/public/feeds/google-shopping.xml` | — | `IActionResult` | Get google shopping feed |
| GET | `/api/public/feeds/cimri.xml` | — | `IActionResult` | Get cimri feed |
| GET | `/api/public/feeds/products.xml` | Query: string? format | `IActionResult` | Get custom feed |

#### Resellers (/api/resellers)
| Method | Path | Request | Response | Purpose |
| --- | --- | --- | --- | --- |
| POST | `/api/resellers` | Body: CreateResellerCommand command | `CreateResellerResponse` | Create reseller |
| GET | `/api/resellers` | Query: GetResellersQuery query | `GetResellersResponse` | Get resellers |
| POST | `/api/resellers/{resellerId}/prices` | Route: Guid resellerId <br> Body: CreateResellerPriceCommand command | `CreateResellerPriceResponse` | Create reseller price |

#### Reviews (/api/reviews)
| Method | Path | Request | Response | Purpose |
| --- | --- | --- | --- | --- |
| GET | `/api/reviews/product/{productId}` | Route: Guid productId <br> Query: int page <br> Query: int pageSize <br> Query: string? sortBy <br> Query: string? sortOrder <br> Query: int? minRating <br> Query: int? maxRating <br> Query: bool? isVerifiedPurchase <br> Query: bool? hasReply <br> Query: bool? onlyWithImages | `GetProductReviewsResponse` | Get product reviews |
| POST | `/api/reviews` | Body: CreateReviewCommand command | `CreateReviewResponse` | Create review |
| PUT | `/api/reviews/{id}` | Route: Guid id <br> Body: UpdateReviewCommand command | `UpdateReviewResponse` | Update review |
| DELETE | `/api/reviews/{id}` | Route: Guid id | `DeleteReviewResponse` | Delete review |
| POST | `/api/reviews/{id}/vote` | Route: Guid id <br> Body: VoteReviewCommand command | `VoteReviewResponse` | Vote review |
| POST | `/api/reviews/{id}/approve` | Route: Guid id <br> Body: ApproveReviewCommand command | `ApproveReviewResponse` | Approve review |
| POST | `/api/reviews/{id}/reply` | Route: Guid id <br> Body: ReplyToReviewCommand command | `ReplyToReviewResponse` | Reply to review |

#### Templates (/api/templates)
| Method | Path | Request | Response | Purpose |
| --- | --- | --- | --- | --- |
| GET | `/api/templates/available` | — | `GetAvailableTemplatesResponse` | Get available templates |
| GET | `/api/templates/selected` | — | `GetSelectedTemplateResponse` | Get selected template |
| POST | `/api/templates/select` | Body: SelectTemplateCommand command | `SelectTemplateResponse` | Select template |

#### Tenant (/api/tenant)
| Method | Path | Request | Response | Purpose |
| --- | --- | --- | --- | --- |
| GET | `/api/tenant/public` | Query: string? slug | `GetTenantPublicInfoResponse` | Get public info |
| GET | `/api/tenant/settings` | — | `GetTenantSettingsResponse` | Get settings |
| PUT | `/api/tenant/settings` | Body: UpdateTenantSettingsCommand command | `UpdateTenantSettingsResponse` | Update settings |
| GET | `/api/tenant/layout` | — | `GetLayoutSettingsResponse` | Get layout settings |
| PUT | `/api/tenant/layout` | Body: UpdateLayoutSettingsCommand command | `UpdateLayoutSettingsResponse` | Update layout settings |


### Tinisoft.Customers.API
Customer storefront auth, profile, cart and checkout flows.

#### Customers (/api/customers)
| Method | Path | Request | Response | Purpose |
| --- | --- | --- | --- | --- |
| POST | `/api/customers/register` | Body: RegisterCustomerCommand command | `CustomerAuthResponse` | Register |
| POST | `/api/customers/login` | Body: LoginCustomerCommand command | `CustomerLoginResponse` | Login |
| GET | `/api/customers/profile` | — | `CustomerDto` | Get profile |
| PUT | `/api/customers/profile` | Body: UpdateCustomerProfileCommand command | `CustomerDto` | Update profile |
| POST | `/api/customers/addresses` | Body: AddCustomerAddressCommand command | `CustomerAddressDto` | Add address |
| GET | `/api/customers/addresses` | — | `List<CustomerAddressDto` | Get addresses |
| GET | `/api/customers/cart` | — | `GetCartResponse` | Get cart |
| POST | `/api/customers/cart/items` | Body: AddCartItemCommand command | `AddCartItemResponse` | Add cart item |
| PUT | `/api/customers/cart/items/{id}` | Route: Guid id <br> Body: UpdateCartItemCommand command | `UpdateCartItemResponse` | Update cart item |
| DELETE | `/api/customers/cart/items/{id}` | Route: Guid id | `RemoveCartItemResponse` | Remove cart item |
| DELETE | `/api/customers/cart` | — | `ClearCartResponse` | Clear cart |
| POST | `/api/customers/orders/checkout` | Body: CheckoutFromCartCommand command | `CheckoutFromCartResponse` | Checkout from cart |
| GET | `/api/customers/orders` | Query: GetCustomerOrdersQuery query | `GetCustomerOrdersResponse` | Get orders |
| GET | `/api/customers/orders/{id}` | Route: Guid id | `GetCustomerOrderResponse` | Get order |
| POST | `/api/customers/cart/apply-coupon` | Body: ApplyCouponToCartCommand command | `ApplyCouponToCartResponse` | Apply coupon to cart |
| DELETE | `/api/customers/cart/coupon` | — | `RemoveCouponFromCartResponse` | Remove coupon from cart |


### Tinisoft.Inventory.API
Standalone inventory synch endpoints for internal jobs.

#### Inventory (/api/inventory)
| Method | Path | Request | Response | Purpose |
| --- | --- | --- | --- | --- |
| GET | `/api/inventory/products/{productId}` | Route: Guid productId <br> Query: Guid? variantId | `GetStockLevelResponse` | Get stock level |
| POST | `/api/inventory/adjust` | Body: AdjustStockCommand command | `AdjustStockResponse` | Adjust stock |


### Tinisoft.Invoices.API
E-invoice creation, GIB integration and settings.

#### Invoices (/api/invoices)
| Method | Path | Request | Response | Purpose |
| --- | --- | --- | --- | --- |
| GET | `/api/invoices` | Query: GetInvoicesQuery query | `GetInvoicesResponse` | Get invoices |
| GET | `/api/invoices/{id}` | Route: Guid id <br> Query: bool includePdf | `GetInvoiceResponse` | Get invoice |
| POST | `/api/invoices` | Body: CreateInvoiceCommand command | `CreateInvoiceResponse` | Create invoice |
| POST | `/api/invoices/{id}/cancel` | Route: Guid id <br> Body: CancelInvoiceCommand command | `CancelInvoiceResponse` | Cancel invoice |
| POST | `/api/invoices/{id}/send-to-gib` | Route: Guid id | `SendInvoiceToGIBResponse` | Send invoice to g i b |
| GET | `/api/invoices/settings` | — | `GetInvoiceSettingsResponse` | Get invoice settings |
| PUT | `/api/invoices/settings` | Body: UpdateInvoiceSettingsCommand command | `UpdateInvoiceSettingsResponse` | Update invoice settings |
| GET | `/api/invoices/{id}/gib-status` | Route: Guid id | `GetInvoiceStatusFromGIBResponse` | Get invoice status from g i b |
| GET | `/api/invoices/inbox` | Query: DateTime? startDate <br> Query: DateTime? endDate <br> Query: string? senderVKN | `GetInboxInvoicesResponse` | Get inbox invoices |


### Tinisoft.Marketplace.API
Marketplace integrations (Trendyol, Hepsiburada, N11).

#### Marketplace (/api/marketplace)
| Method | Path | Request | Response | Purpose |
| --- | --- | --- | --- | --- |
| POST | `/api/marketplace/sync/products` | Body: SyncProductsCommand command | `SyncProductsResponse` | Sync products |


### Tinisoft.Notifications.API
Transactional email providers/templates and send flows.

#### Notifications (/api/notifications)
| Method | Path | Request | Response | Purpose |
| --- | --- | --- | --- | --- |
| POST | `/api/notifications/email-providers` | Body: CreateEmailProviderCommand command | `CreateEmailProviderResponse` | Create email provider |
| POST | `/api/notifications/email-templates` | Body: CreateEmailTemplateCommand command | `CreateEmailTemplateResponse` | Create email template |
| GET | `/api/notifications/email-templates` | Query: GetEmailTemplatesQuery query | `GetEmailTemplatesResponse` | Get email templates |
| POST | `/api/notifications/send-email` | Body: SendEmailCommand command | `SendEmailResponse` | Send email |


### Tinisoft.Orders.API
Order creation, lookup and status updates.

#### Orders (/api/orders)
| Method | Path | Request | Response | Purpose |
| --- | --- | --- | --- | --- |
| POST | `/api/orders` | Body: CreateOrderCommand command | `CreateOrderResponse` | Create order |
| GET | `/api/orders/{id}` | Route: Guid id | `GetOrderResponse` | Get order |
| PUT | `/api/orders/{id}/status` | Route: Guid id <br> Body: UpdateOrderStatusCommand command | `UpdateOrderStatusResponse` | Update order status |


### Tinisoft.Payments.API
Payments orchestration + PayTR callbacks.

#### Payments (/api/payments)
| Method | Path | Request | Response | Purpose |
| --- | --- | --- | --- | --- |
| POST | `/api/payments/process` | Body: ProcessPaymentCommand command | `ProcessPaymentResponse` | Process payment |
| POST | `/api/payments/verify` | Body: VerifyPaymentCommand command | `VerifyPaymentResponse` | Verify payment |
| POST | `/api/payments/callback/paytr` | Form: Dictionary<string, string> data | `IActionResult` | Pay t r callback |


### Tinisoft.Products.API
Product catalog (admin + storefront) and tax utilities.

#### Products (/api/products)
| Method | Path | Request | Response | Purpose |
| --- | --- | --- | --- | --- |
| GET | `/api/products` | Query: GetProductsQuery query | `GetProductsResponse` | Get products |
| GET | `/api/products/{id}` | Route: Guid id | `GetProductResponse` | Get product |
| POST | `/api/products` | Body: CreateProductCommand command | `CreateProductResponse` | Create product |
| PUT | `/api/products/{id}` | Route: Guid id <br> Body: UpdateProductCommand command | `UpdateProductResponse` | Update product |
| DELETE | `/api/products/{id}` | Route: Guid id | `IActionResult` | Delete product |

#### Storefront (/api/storefront)
| Method | Path | Request | Response | Purpose |
| --- | --- | --- | --- | --- |
| GET | `/api/storefront/products` | Query: GetStorefrontProductsQuery query | `GetStorefrontProductsResponse` | Get products |
| GET | `/api/storefront/products/{id}` | Route: Guid id <br> Query: string? preferredCurrency | `GetStorefrontProductResponse` | Get product |
| GET | `/api/storefront/categories` | — | `GetStorefrontCategoriesResponse` | Get categories |

#### Tax (/api/tax)
| Method | Path | Request | Response | Purpose |
| --- | --- | --- | --- | --- |
| POST | `/api/tax/calculate` | Body: CalculateTaxCommand command | `CalculateTaxResponse` | Calculate tax |
| GET | `/api/tax/rates` | Query: bool? isActive | `List<TaxRateDto` | Get tax rates |
| POST | `/api/tax/rates` | Body: CreateTaxRateCommand command | `CreateTaxRateResponse` | Create tax rate |
| PUT | `/api/tax/rates/{id}` | Route: Guid id <br> Body: UpdateTaxRateCommand command | `UpdateTaxRateResponse` | Update tax rate |
| DELETE | `/api/tax/rates/{id}` | Route: Guid id | `IActionResult` | Delete tax rate |


### Tinisoft.Shipping.API
Shipping providers, cost calculation, shipment creation.

#### Shipping (/api/shipping)
| Method | Path | Request | Response | Purpose |
| --- | --- | --- | --- | --- |
| GET | `/api/shipping/providers` | Query: GetShippingProvidersQuery query | `GetShippingProvidersResponse` | Get shipping providers |
| POST | `/api/shipping/providers` | Body: CreateShippingProviderCommand command | `CreateShippingProviderResponse` | Create shipping provider |
| PUT | `/api/shipping/providers/{id}` | Route: Guid id <br> Body: UpdateShippingProviderCommand command | `UpdateShippingProviderResponse` | Update shipping provider |
| POST | `/api/shipping/calculate-cost` | Body: CalculateShippingCostCommand command | `CalculateShippingCostResponse` | Calculate shipping cost |
| POST | `/api/shipping/shipments` | Body: CreateShipmentCommand command | `CreateShipmentResponse` | Create shipment |

