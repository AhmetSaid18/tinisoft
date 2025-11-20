using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Application.Common.Interfaces;
using Tinisoft.Shared.Contracts;
using Tinisoft.Application.Common.Interfaces;
using Finbuckle.MultiTenant;

namespace Tinisoft.Application.Customers.Queries.GetCart;

public class GetCartQueryHandler : IRequestHandler<GetCartQuery, GetCartResponse>
{
    private readonly IApplicationDbContext _dbContext;
    private readonly ICurrentCustomerService _currentCustomerService;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly ILogger<GetCartQueryHandler> _logger;

    public GetCartQueryHandler(
        IApplicationDbContext dbContext,
        ICurrentCustomerService currentCustomerService,
        IMultiTenantContextAccessor tenantAccessor,
        ILogger<GetCartQueryHandler> logger)
    {
        _dbContext = dbContext;
        _currentCustomerService = currentCustomerService;
        _tenantAccessor = tenantAccessor;
        _logger = logger;
    }

    public async Task<GetCartResponse> Handle(GetCartQuery request, CancellationToken cancellationToken)
    {
        var customerId = _currentCustomerService.GetCurrentCustomerId();
        if (!customerId.HasValue)
        {
            throw new UnauthorizedAccessException("Müşteri bilgisi bulunamadı");
        }

        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        // Cart'ı getir veya oluştur
        var cart = await _dbContext.Carts
            .Include(c => c.Items)
                .ThenInclude(ci => ci.Product)
                    .ThenInclude(p => p.Images.OrderBy(img => img.Position).Take(1))
            .Include(c => c.Coupon)
            
            .FirstOrDefaultAsync(c => c.TenantId == tenantId && c.CustomerId == customerId.Value, cancellationToken);

        if (cart == null)
        {
            // Yeni cart oluştur
            cart = new Domain.Entities.Cart
            {
                TenantId = tenantId,
                CustomerId = customerId.Value,
                Currency = "TRY",
                LastUpdatedAt = DateTime.UtcNow
            };
            _dbContext.Carts.Add(cart);
            await _dbContext.SaveChangesAsync(cancellationToken);
            
            // Yeni cart için Items boş liste
            return new GetCartResponse
            {
                CartId = cart.Id,
                Items = new List<CartItemDto>(),
                Subtotal = 0,
                Tax = 0,
                Shipping = 0,
                Discount = 0,
                Total = 0,
                Currency = cart.Currency,
                LastUpdatedAt = cart.LastUpdatedAt
            };
        }

        // Response mapping
        var items = cart.Items.Select(ci => new CartItemDto
        {
            Id = ci.Id,
            ProductId = ci.ProductId,
            ProductVariantId = ci.ProductVariantId,
            Title = ci.Title,
            SKU = ci.SKU,
            Quantity = ci.Quantity,
            UnitPrice = ci.UnitPrice,
            TotalPrice = ci.TotalPrice,
            Currency = ci.Currency,
            ProductImageUrl = ci.Product?.Images.FirstOrDefault()?.OriginalUrl
        }).ToList();

        return new GetCartResponse
        {
            CartId = cart.Id,
            Items = items,
            CouponCode = cart.CouponCode,
            CouponName = cart.Coupon?.Name,
            Subtotal = cart.Subtotal,
            Tax = cart.Tax,
            Shipping = cart.Shipping,
            Discount = cart.Discount,
            Total = cart.Total,
            Currency = cart.Currency,
            LastUpdatedAt = cart.LastUpdatedAt
        };
    }
}



