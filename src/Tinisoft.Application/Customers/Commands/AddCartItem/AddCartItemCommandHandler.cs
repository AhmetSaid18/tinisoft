using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Infrastructure.Persistence;
using Tinisoft.Application.Common.Interfaces;
using Finbuckle.MultiTenant;

namespace Tinisoft.Application.Customers.Commands.AddCartItem;

public class AddCartItemCommandHandler : IRequestHandler<AddCartItemCommand, AddCartItemResponse>
{
    private readonly ApplicationDbContext _dbContext;
    private readonly ICurrentCustomerService _currentCustomerService;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly ILogger<AddCartItemCommandHandler> _logger;

    public AddCartItemCommandHandler(
        ApplicationDbContext dbContext,
        ICurrentCustomerService currentCustomerService,
        IMultiTenantContextAccessor tenantAccessor,
        ILogger<AddCartItemCommandHandler> logger)
    {
        _dbContext = dbContext;
        _currentCustomerService = currentCustomerService;
        _tenantAccessor = tenantAccessor;
        _logger = logger;
    }

    public async Task<AddCartItemResponse> Handle(AddCartItemCommand request, CancellationToken cancellationToken)
    {
        var customerId = _currentCustomerService.GetCurrentCustomerId();
        if (!customerId.HasValue)
        {
            throw new UnauthorizedAccessException("Müşteri bilgisi bulunamadı");
        }

        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        // Product'ı kontrol et
        var product = await _dbContext.Products
            .AsNoTracking()
            .FirstOrDefaultAsync(p => p.Id == request.ProductId && p.TenantId == tenantId && p.IsActive && p.Status == "Active", cancellationToken);

        if (product == null)
        {
            throw new KeyNotFoundException("Ürün bulunamadı veya aktif değil");
        }

        // Variant kontrolü
        decimal unitPrice = product.Price;
        string? sku = product.SKU;
        if (request.ProductVariantId.HasValue)
        {
            var variant = await _dbContext.ProductVariants
                .AsNoTracking()
                .FirstOrDefaultAsync(v => v.Id == request.ProductVariantId.Value && v.ProductId == request.ProductId, cancellationToken);

            if (variant == null)
            {
                throw new KeyNotFoundException("Ürün varyantı bulunamadı");
            }

            unitPrice = variant.Price;
            sku = variant.SKU ?? product.SKU;
        }

        // Stok kontrolü
        if (product.TrackInventory && product.InventoryQuantity.HasValue)
        {
            var availableQuantity = product.InventoryQuantity.Value;
            if (availableQuantity < request.Quantity && !product.AllowBackorder)
            {
                throw new InvalidOperationException($"Yeterli stok yok. Mevcut stok: {availableQuantity}");
            }
        }

        // Cart'ı getir veya oluştur
        var cart = await _dbContext.Carts
            .Include(c => c.Items)
            .FirstOrDefaultAsync(c => c.TenantId == tenantId && c.CustomerId == customerId.Value, cancellationToken);

        if (cart == null)
        {
            cart = new Domain.Entities.Cart
            {
                TenantId = tenantId,
                CustomerId = customerId.Value,
                Currency = product.Currency ?? "TRY",
                LastUpdatedAt = DateTime.UtcNow
            };
            _dbContext.Carts.Add(cart);
            await _dbContext.SaveChangesAsync(cancellationToken);
        }

        // Aynı ürün/variant zaten sepette var mı?
        var existingItem = cart.Items.FirstOrDefault(ci =>
            ci.ProductId == request.ProductId &&
            ci.ProductVariantId == request.ProductVariantId);

        if (existingItem != null)
        {
            // Miktarı artır
            existingItem.Quantity += request.Quantity;
            existingItem.TotalPrice = existingItem.Quantity * existingItem.UnitPrice;
        }
        else
        {
            // Yeni item ekle
            var cartItem = new Domain.Entities.CartItem
            {
                CartId = cart.Id,
                ProductId = request.ProductId,
                ProductVariantId = request.ProductVariantId,
                Title = product.Title,
                SKU = sku,
                Quantity = request.Quantity,
                UnitPrice = unitPrice,
                TotalPrice = request.Quantity * unitPrice,
                Currency = product.Currency ?? "TRY"
            };
            _dbContext.CartItems.Add(cartItem);
            cart.Items.Add(cartItem);
        }

        // Cart totals'ı hesapla
        cart.Subtotal = cart.Items.Sum(ci => ci.TotalPrice);
        cart.Tax = 0; // Tax calculation sonra eklenecek
        cart.Shipping = 0; // Shipping calculation sonra eklenecek
        cart.Discount = 0; // Discount calculation sonra eklenecek
        cart.Total = cart.Subtotal + cart.Tax + cart.Shipping - cart.Discount;
        cart.LastUpdatedAt = DateTime.UtcNow;

        await _dbContext.SaveChangesAsync(cancellationToken);

        var addedItem = existingItem ?? cart.Items.Last();
        return new AddCartItemResponse
        {
            CartItemId = addedItem.Id,
            CartId = cart.Id,
            Item = new CartItemDto
            {
                Id = addedItem.Id,
                ProductId = addedItem.ProductId,
                ProductVariantId = addedItem.ProductVariantId,
                Title = addedItem.Title,
                SKU = addedItem.SKU,
                Quantity = addedItem.Quantity,
                UnitPrice = addedItem.UnitPrice,
                TotalPrice = addedItem.TotalPrice,
                Currency = addedItem.Currency
            },
            CartTotal = cart.Total
        };
    }
}

