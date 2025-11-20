# Customers Microservice API

**Service:** `Tinisoft.Customers.API`  
**Base Path:** `/api/customers`  
**Auth:**
- `[Public]` uçlar (register/login) token gerektirmez.
- Diğer tüm uçlar `[RequireRole("Customer")]` ve müşteri JWT'si ister (gateway `x-tenant-id` gibi header'ları otomatik ekler).

---

## 1. Kimlik Doğrulama

### POST `/api/customers/register`
- **Body (`RegisterCustomerCommand`):**
  - `email` (string, zorunlu)
  - `password` (string, zorunlu)
  - `firstName`, `lastName`, `phone` (opsiyonel)
- **Response (`CustomerAuthResponse`):** `customerId`, `email`, `firstName`, `lastName`, `phone`, `token`.

### POST `/api/customers/login`
- **Body (`LoginCustomerCommand`):** `email`, `password`.
- **Response (`CustomerLoginResponse`):** `customerId`, `email`, `firstName`, `lastName`, `phone`, `token`.

Token müşterinin diğer uçlara erişimi için Authorization header'ında `Bearer {token}` olarak gönderilir.

---

## 2. Profil & Adresler

### GET `/api/customers/profile`
- **Response (`CustomerDto`):** `id`, `email`, `firstName`, `lastName`, `phone`, `emailVerified`, `createdAt`.

### PUT `/api/customers/profile`
- **Body (`UpdateCustomerProfileCommand`):**
  - `firstName`, `lastName`, `phone`
  - `password` (mevcut parola, opsiyonel ama parola değişimi yapılacaksa zorunlu)
  - `newPassword`
- **Response:** Güncel `CustomerDto`.

### POST `/api/customers/addresses`
- **Body (`AddCustomerAddressCommand`):**
  - `addressLine1`*, `addressLine2`
  - `city`*, `state`, `postalCode`*, `country` (varsayılan `TR`)
  - `phone`, `addressTitle`
  - `isDefaultShipping`, `isDefaultBilling` (bool)
- **Response (`CustomerAddressDto`):** `addressId` ve aynı alanlar.

### GET `/api/customers/addresses`
- **Response:** `CustomerAddressDto[]`.

---

## 3. Sepet İşlemleri

### GET `/api/customers/cart`
- **Response (`GetCartResponse`):**
  - `cartId`
  - `items[]` (`CartItemDto`: `id`, `productId`, `productVariantId`, `title`, `sku`, `quantity`, `unitPrice`, `totalPrice`, `currency`, `productImageUrl`)
  - `couponCode`, `couponName`
  - `subtotal`, `tax`, `shipping`, `discount`, `total`
  - `currency`, `lastUpdatedAt`

### POST `/api/customers/cart/items`
- **Body (`AddCartItemCommand`):** `productId`, `productVariantId`, `quantity` (varsayılan 1).
- **Response (`AddCartItemResponse`):** `cartItemId`, `cartId`, `item` (`CartItemDto`), `cartTotal`.

### PUT `/api/customers/cart/items/{id}`
- **Path Param:** `id` → hedef `cartItemId`.
- **Body (`UpdateCartItemCommand`):** `quantity`.
- **Response (`UpdateCartItemResponse`):** `cartItemId`, `item`, `cartTotal`.

### DELETE `/api/customers/cart/items/{id}`
- **Response (`RemoveCartItemResponse`):** `success`, `cartTotal`.

### DELETE `/api/customers/cart`
- **Response (`ClearCartResponse`):** `success`.

---

## 4. Kupon Yönetimi

### POST `/api/customers/cart/apply-coupon`
- **Body (`ApplyCouponToCartCommand`):** `couponCode`.
- **Response (`ApplyCouponToCartResponse`):** `success`, `errorMessage`, `couponCode`, `couponName`, `discountAmount`, `cartTotal`.

### DELETE `/api/customers/cart/coupon`
- **Response (`RemoveCouponFromCartResponse`):** `success`, `cartTotal`.

---

## 5. Checkout & Siparişler

### POST `/api/customers/orders/checkout`
- **Body (`CheckoutFromCartCommand`):**
  - Kargo adresi: `shippingAddressId` (kayıtlı adres) veya manuel `shippingAddressLine1/2`, `shippingCity`, `shippingState`, `shippingPostalCode`, `shippingCountry`
  - `shippingMethod`
  - Ödeme: `paymentProvider`
  - `orderNotes`
- **Response (`CheckoutFromCartResponse`):** `orderId`, `orderNumber`, `total`, `status`, `paymentUrl`.

### GET `/api/customers/orders`
- **Query (`GetCustomerOrdersQuery`):**
  - `page` (varsayılan 1)
  - `pageSize` (varsayılan 20)
  - `status` (`Pending`, `Paid`, `Processing`, `Shipped`, `Delivered`, `Cancelled`)
- **Response (`GetCustomerOrdersResponse`):**
  - `orders[]` (`CustomerOrderDto`: `id`, `orderNumber`, `status`, `total`, `currency`, `paymentStatus`, `shippingMethod`, `trackingNumber`, `createdAt`, `itemCount`)
  - `totalCount`, `page`, `pageSize`, `totalPages`

### GET `/api/customers/orders/{id}`
- **Response (`GetCustomerOrderResponse`):**
  - Kimlik: `id`, `orderNumber`, `status`
  - Müşteri: `customerEmail`, `customerPhone`, `customerFirstName`, `customerLastName`
  - Kargo adresi (`ShippingAddressDto`): `addressLine1`, `addressLine2`, `city`, `state`, `postalCode`, `country`
  - Toplamlar (`OrderTotalsDto`): `subtotal`, `tax`, `shipping`, `discount`, `total`
  - Ödeme: `paymentStatus`, `paymentProvider`, `paidAt`
  - Kargo: `shippingMethod`, `trackingNumber`
  - Kalemler (`OrderItemDto[]`): `id`, `productId`, `productVariantId`, `title`, `sku`, `quantity`, `unitPrice`, `totalPrice`
  - `createdAt`, `updatedAt`

---

## Notlar
- Tüm müşteri çağrıları tenant bağlamında çalışır; gateway `X-Tenant-Id` veya benzeri header'ları eklemelidir.
- Sepet işlemleri concurrency için optimistic locking kullanır; UI aynı `cartId` üzerinde `lastUpdatedAt` ile eşitlemelidir (ileride eklenecek).
- Checkout çıktısındaki `paymentUrl` progressive entegrasyon için placeholder; boş gelirse ödemeyi Merchant Panel'den tamamlayın.

