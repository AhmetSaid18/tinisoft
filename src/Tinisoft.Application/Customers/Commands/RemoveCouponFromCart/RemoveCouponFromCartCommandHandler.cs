using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Application.Common.Interfaces;
using Tinisoft.Shared.Contracts;
using Tinisoft.Application.Common.Interfaces;
using Finbuckle.MultiTenant;

namespace Tinisoft.Application.Customers.Commands.RemoveCouponFromCart;

public class RemoveCouponFromCartCommandHandler : IRequestHandler<RemoveCouponFromCartCommand, RemoveCouponFromCartResponse>
{
    private readonly IApplicationDbContext _dbContext;
    private readonly ICurrentCustomerService _currentCustomerService;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly ILogger<RemoveCouponFromCartCommandHandler> _logger;

    public RemoveCouponFromCartCommandHandler(
        IApplicationDbContext dbContext,
        ICurrentCustomerService currentCustomerService,
        IMultiTenantContextAccessor tenantAccessor,
        ILogger<RemoveCouponFromCartCommandHandler> logger)
    {
        _dbContext = dbContext;
        _currentCustomerService = currentCustomerService;
        _tenantAccessor = tenantAccessor;
        _logger = logger;
    }

    public async Task<RemoveCouponFromCartResponse> Handle(RemoveCouponFromCartCommand request, CancellationToken cancellationToken)
    {
        var customerId = _currentCustomerService.GetCurrentCustomerId();
        if (!customerId.HasValue)
        {
            throw new UnauthorizedAccessException("Müşteri bilgisi bulunamadı");
        }

        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        // Cart'ı getir
        var cart = await _dbContext.Carts
            .FirstOrDefaultAsync(c => c.TenantId == tenantId && c.CustomerId == customerId.Value, cancellationToken);

        if (cart == null)
        {
            return new RemoveCouponFromCartResponse
            {
                Success = true,
                CartTotal = 0
            };
        }

        // Kuponu kaldır
        cart.CouponCode = null;
        cart.CouponId = null;
        cart.Discount = 0;
        cart.Total = cart.Subtotal + cart.Tax + cart.Shipping - cart.Discount;
        cart.LastUpdatedAt = DateTime.UtcNow;

        await _dbContext.SaveChangesAsync(cancellationToken);

        return new RemoveCouponFromCartResponse
        {
            Success = true,
            CartTotal = cart.Total
        };
    }
}



