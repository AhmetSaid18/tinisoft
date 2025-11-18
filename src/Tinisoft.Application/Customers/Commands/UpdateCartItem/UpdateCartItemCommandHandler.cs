using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Infrastructure.Persistence;
using Tinisoft.Application.Common.Interfaces;
using Finbuckle.MultiTenant;

namespace Tinisoft.Application.Customers.Commands.UpdateCartItem;

public class UpdateCartItemCommandHandler : IRequestHandler<UpdateCartItemCommand, UpdateCartItemResponse>
{
    private readonly ApplicationDbContext _dbContext;
    private readonly ICurrentCustomerService _currentCustomerService;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly ILogger<UpdateCartItemCommandHandler> _logger;

    public UpdateCartItemCommandHandler(
        ApplicationDbContext dbContext,
        ICurrentCustomerService currentCustomerService,
        IMultiTenantContextAccessor tenantAccessor,
        ILogger<UpdateCartItemCommandHandler> logger)
    {
        _dbContext = dbContext;
        _currentCustomerService = currentCustomerService;
        _tenantAccessor = tenantAccessor;
        _logger = logger;
    }

    public async Task<UpdateCartItemResponse> Handle(UpdateCartItemCommand request, CancellationToken cancellationToken)
    {
        var customerId = _currentCustomerService.GetCurrentCustomerId();
        if (!customerId.HasValue)
        {
            throw new UnauthorizedAccessException("Müşteri bilgisi bulunamadı");
        }

        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        if (request.Quantity <= 0)
        {
            throw new ArgumentException("Miktar 0'dan büyük olmalıdır");
        }

        // CartItem'ı getir
        var cartItem = await _dbContext.CartItems
            .Include(ci => ci.Cart)
            .Include(ci => ci.Product)
            .FirstOrDefaultAsync(ci => ci.Id == request.CartItemId && 
                ci.Cart.TenantId == tenantId && 
                ci.Cart.CustomerId == customerId.Value, cancellationToken);

        if (cartItem == null)
        {
            throw new KeyNotFoundException("Sepet öğesi bulunamadı");
        }

        // Stok kontrolü
        if (cartItem.Product.TrackInventory && cartItem.Product.InventoryQuantity.HasValue)
        {
            var availableQuantity = cartItem.Product.InventoryQuantity.Value;
            if (availableQuantity < request.Quantity && !cartItem.Product.AllowBackorder)
            {
                throw new InvalidOperationException($"Yeterli stok yok. Mevcut stok: {availableQuantity}");
            }
        }

        // Miktarı güncelle
        cartItem.Quantity = request.Quantity;
        cartItem.TotalPrice = cartItem.Quantity * cartItem.UnitPrice;

        // Cart totals'ı hesapla
        var cart = cartItem.Cart;
        cart.Subtotal = cart.Items.Sum(ci => ci.TotalPrice);
        cart.Tax = 0;
        cart.Shipping = 0;
        cart.Discount = 0;
        cart.Total = cart.Subtotal + cart.Tax + cart.Shipping - cart.Discount;
        cart.LastUpdatedAt = DateTime.UtcNow;

        await _dbContext.SaveChangesAsync(cancellationToken);

        return new UpdateCartItemResponse
        {
            CartItemId = cartItem.Id,
            Item = new CartItemDto
            {
                Id = cartItem.Id,
                ProductId = cartItem.ProductId,
                ProductVariantId = cartItem.ProductVariantId,
                Title = cartItem.Title,
                SKU = cartItem.SKU,
                Quantity = cartItem.Quantity,
                UnitPrice = cartItem.UnitPrice,
                TotalPrice = cartItem.TotalPrice,
                Currency = cartItem.Currency
            },
            CartTotal = cart.Total
        };
    }
}

