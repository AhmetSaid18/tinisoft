using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Infrastructure.Persistence;
using Tinisoft.Application.Common.Interfaces;
using Tinisoft.Shared.Events;
using Finbuckle.MultiTenant;
using System.Text.Json;

namespace Tinisoft.Application.Customers.Commands.CheckoutFromCart;

public class CheckoutFromCartCommandHandler : IRequestHandler<CheckoutFromCartCommand, CheckoutFromCartResponse>
{
    private readonly ApplicationDbContext _dbContext;
    private readonly ICurrentCustomerService _currentCustomerService;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly IEventBus _eventBus;
    private readonly ILogger<CheckoutFromCartCommandHandler> _logger;

    public CheckoutFromCartCommandHandler(
        ApplicationDbContext dbContext,
        ICurrentCustomerService currentCustomerService,
        IMultiTenantContextAccessor tenantAccessor,
        IEventBus eventBus,
        ILogger<CheckoutFromCartCommandHandler> logger)
    {
        _dbContext = dbContext;
        _currentCustomerService = currentCustomerService;
        _tenantAccessor = tenantAccessor;
        _eventBus = eventBus;
        _logger = logger;
    }

    public async Task<CheckoutFromCartResponse> Handle(CheckoutFromCartCommand request, CancellationToken cancellationToken)
    {
        var customerId = _currentCustomerService.GetCurrentCustomerId();
        if (!customerId.HasValue)
        {
            throw new UnauthorizedAccessException("Müşteri bilgisi bulunamadı");
        }

        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        // Customer bilgilerini al
        var customer = await _dbContext.Customers
            .AsNoTracking()
            .FirstOrDefaultAsync(c => c.Id == customerId.Value && c.TenantId == tenantId, cancellationToken);

        if (customer == null)
        {
            throw new KeyNotFoundException("Müşteri bulunamadı");
        }

        // Cart'ı getir (Product bilgileriyle birlikte)
        var cart = await _dbContext.Carts
            .Include(c => c.Items)
                .ThenInclude(ci => ci.Product)
            .AsSplitQuery()
            .FirstOrDefaultAsync(c => c.TenantId == tenantId && c.CustomerId == customerId.Value, cancellationToken);

        if (cart == null || !cart.Items.Any())
        {
            throw new InvalidOperationException("Sepet boş veya bulunamadı");
        }

        // Shipping address'i belirle
        string? shippingAddressLine1 = null;
        string? shippingAddressLine2 = null;
        string? shippingCity = null;
        string? shippingState = null;
        string? shippingPostalCode = null;
        string? shippingCountry = null;

        if (request.ShippingAddressId.HasValue)
        {
            // Kayıtlı adresi kullan
            var address = await _dbContext.CustomerAddresses
                .AsNoTracking()
                .FirstOrDefaultAsync(a => a.Id == request.ShippingAddressId.Value && 
                    a.CustomerId == customerId.Value && 
                    a.TenantId == tenantId, cancellationToken);

            if (address == null)
            {
                throw new KeyNotFoundException("Adres bulunamadı");
            }

            shippingAddressLine1 = address.AddressLine1;
            shippingAddressLine2 = address.AddressLine2;
            shippingCity = address.City;
            shippingState = address.State;
            shippingPostalCode = address.PostalCode;
            shippingCountry = address.Country;
        }
        else if (!string.IsNullOrEmpty(request.ShippingAddressLine1))
        {
            // Manuel adres
            shippingAddressLine1 = request.ShippingAddressLine1;
            shippingAddressLine2 = request.ShippingAddressLine2;
            shippingCity = request.ShippingCity;
            shippingState = request.ShippingState;
            shippingPostalCode = request.ShippingPostalCode;
            shippingCountry = request.ShippingCountry;
        }
        else
        {
            throw new ArgumentException("Teslimat adresi belirtilmelidir");
        }

        // Order number oluştur
        var orderCount = await _dbContext.Orders
            .CountAsync(o => o.TenantId == tenantId, cancellationToken);
        var orderNumber = $"ORD-{DateTime.UtcNow:yyyyMMdd}-{orderCount + 1:D6}";

        // Order oluştur
        var order = new Domain.Entities.Order
        {
            TenantId = tenantId,
            OrderNumber = orderNumber,
            Status = "Pending",
            CustomerId = customerId.Value,
            CustomerEmail = customer.Email,
            CustomerPhone = customer.Phone,
            CustomerFirstName = customer.FirstName,
            CustomerLastName = customer.LastName,
            ShippingAddressLine1 = shippingAddressLine1,
            ShippingAddressLine2 = shippingAddressLine2,
            ShippingCity = shippingCity,
            ShippingState = shippingState,
            ShippingPostalCode = shippingPostalCode,
            ShippingCountry = shippingCountry,
            ShippingMethod = request.ShippingMethod,
            PaymentStatus = "Pending",
            PaymentProvider = request.PaymentProvider,
            CouponCode = cart.CouponCode,
            CouponId = cart.CouponId,
            TotalsJson = JsonSerializer.Serialize(new
            {
                subtotal = cart.Subtotal,
                tax = cart.Tax,
                shipping = cart.Shipping,
                discount = cart.Discount,
                total = cart.Total
            })
        };

        _dbContext.Orders.Add(order);

        // Order Items (Cart'tan) - Stok kontrolü ve rezervasyonu
        foreach (var cartItem in cart.Items)
        {
            // Stok kontrolü ve rezervasyonu (ProductInventory tablosundan)
            if (cartItem.Product.TrackInventory)
            {
                // Warehouse bazlı stok kontrolü - Tüm warehouse'ların toplam available quantity'sini kontrol et
                var totalAvailableQuantity = await _dbContext.Set<Domain.Entities.ProductInventory>()
                    .Where(pi => 
                        pi.ProductId == cartItem.ProductId &&
                        pi.TenantId == tenantId &&
                        pi.IsActive)
                    .SumAsync(pi => pi.AvailableQuantity, cancellationToken);

                if (totalAvailableQuantity < cartItem.Quantity && !cartItem.Product.AllowBackorder)
                {
                    throw new InvalidOperationException(
                        $"Ürün stokta yok: {cartItem.Product.Title}. Mevcut stok: {totalAvailableQuantity}, İstenen: {cartItem.Quantity}");
                }

                // Stok rezervasyonu - FIFO mantığı ile en uygun warehouse'dan rezerve et
                var remainingQuantity = cartItem.Quantity;
                var inventories = await _dbContext.Set<Domain.Entities.ProductInventory>()
                    .Include(pi => pi.Warehouse)
                    .Include(pi => pi.WarehouseLocation)
                    .Where(pi => 
                        pi.ProductId == cartItem.ProductId &&
                        pi.TenantId == tenantId &&
                        pi.IsActive &&
                        pi.AvailableQuantity > 0)
                    .OrderBy(pi => pi.InventoryMethod == "FIFO" ? pi.CreatedAt : DateTime.MaxValue) // FIFO için en eski
                    .ThenByDescending(pi => pi.InventoryMethod == "LIFO" ? pi.CreatedAt : DateTime.MinValue) // LIFO için en yeni
                    .ThenBy(pi => pi.ExpiryDate ?? DateTime.MaxValue) // FEFO için son kullanma tarihi
                    .ToListAsync(cancellationToken);

                foreach (var inventory in inventories)
                {
                    if (remainingQuantity <= 0) break;

                    var quantityToReserve = Math.Min(remainingQuantity, inventory.AvailableQuantity);
                    
                    // Rezerve et
                    inventory.ReservedQuantity += quantityToReserve;
                    remainingQuantity -= quantityToReserve;

                    // StockMovement kaydı oluştur (RESERVED)
                    var stockMovement = new Domain.Entities.StockMovement
                    {
                        TenantId = tenantId,
                        ProductId = cartItem.ProductId,
                        ProductVariantId = cartItem.ProductVariantId,
                        WarehouseId = inventory.WarehouseId,
                        WarehouseLocationId = inventory.WarehouseLocationId,
                        MovementType = "RESERVED",
                        Quantity = -quantityToReserve, // Negatif çünkü rezerve edildi
                        QuantityBefore = inventory.Quantity - inventory.ReservedQuantity + quantityToReserve,
                        QuantityAfter = inventory.Quantity - inventory.ReservedQuantity,
                        ReferenceId = order.Id,
                        ReferenceType = "Order",
                        ReferenceNumber = orderNumber,
                        Reason = "Sipariş Rezervasyonu",
                        Notes = $"Order: {orderNumber} - Cart checkout"
                    };
                    _dbContext.Set<Domain.Entities.StockMovement>().Add(stockMovement);
                }

                if (remainingQuantity > 0 && !cartItem.Product.AllowBackorder)
                {
                    throw new InvalidOperationException(
                        $"Yetersiz stok: {cartItem.Product.Title}. Rezerve edilemeyen miktar: {remainingQuantity}");
                }
            }

            var orderItem = new Domain.Entities.OrderItem
            {
                OrderId = order.Id,
                ProductId = cartItem.ProductId,
                ProductVariantId = cartItem.ProductVariantId,
                Title = cartItem.Title,
                SKU = cartItem.SKU,
                Quantity = cartItem.Quantity,
                UnitPrice = cartItem.UnitPrice,
                TotalPrice = cartItem.TotalPrice
            };
            _dbContext.OrderItems.Add(orderItem);
        }

        // Coupon usage kaydı oluştur (eğer kupon kullanıldıysa)
        if (cart.CouponId.HasValue)
        {
            var couponUsage = new Domain.Entities.CouponUsage
            {
                TenantId = tenantId,
                CouponId = cart.CouponId.Value,
                CustomerId = customerId.Value,
                OrderId = order.Id,
                DiscountAmount = cart.Discount,
                UsedAt = DateTime.UtcNow
            };
            _dbContext.CouponUsages.Add(couponUsage);

            // Coupon usage count'u artır
            var coupon = await _dbContext.Coupons.FindAsync(new object[] { cart.CouponId.Value }, cancellationToken);
            if (coupon != null)
            {
                coupon.UsageCount++;
            }
        }

        // Cart'ı temizle
        _dbContext.CartItems.RemoveRange(cart.Items);
        cart.Subtotal = 0;
        cart.Tax = 0;
        cart.Shipping = 0;
        cart.Discount = 0;
        cart.Total = 0;
        cart.CouponCode = null;
        cart.CouponId = null;
        cart.LastUpdatedAt = DateTime.UtcNow;

        await _dbContext.SaveChangesAsync(cancellationToken);

        // Event publish
        await _eventBus.PublishAsync(new OrderCreatedEvent
        {
            OrderId = order.Id,
            TenantId = tenantId,
            OrderNumber = order.OrderNumber,
            TotalAmount = cart.Total
        }, cancellationToken);

        _logger.LogInformation("Order created from cart: {OrderNumber} - Customer: {CustomerId} - Total: {Total}", 
            order.OrderNumber, customerId.Value, cart.Total);

        return new CheckoutFromCartResponse
        {
            OrderId = order.Id,
            OrderNumber = order.OrderNumber,
            Total = cart.Total,
            Status = order.Status,
            PaymentUrl = null // İleride payment provider entegrasyonu ile doldurulacak
        };
    }
}

