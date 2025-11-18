using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Infrastructure.Persistence;
using Tinisoft.Application.Common.Interfaces;
using Finbuckle.MultiTenant;

namespace Tinisoft.Application.Customers.Commands.ClearCart;

public class ClearCartCommandHandler : IRequestHandler<ClearCartCommand, ClearCartResponse>
{
    private readonly ApplicationDbContext _dbContext;
    private readonly ICurrentCustomerService _currentCustomerService;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly ILogger<ClearCartCommandHandler> _logger;

    public ClearCartCommandHandler(
        ApplicationDbContext dbContext,
        ICurrentCustomerService currentCustomerService,
        IMultiTenantContextAccessor tenantAccessor,
        ILogger<ClearCartCommandHandler> logger)
    {
        _dbContext = dbContext;
        _currentCustomerService = currentCustomerService;
        _tenantAccessor = tenantAccessor;
        _logger = logger;
    }

    public async Task<ClearCartResponse> Handle(ClearCartCommand request, CancellationToken cancellationToken)
    {
        var customerId = _currentCustomerService.GetCurrentCustomerId();
        if (!customerId.HasValue)
        {
            throw new UnauthorizedAccessException("Müşteri bilgisi bulunamadı");
        }

        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        // Cart'ı getir
        var cart = await _dbContext.Carts
            .Include(c => c.Items)
            .FirstOrDefaultAsync(c => c.TenantId == tenantId && c.CustomerId == customerId.Value, cancellationToken);

        if (cart == null)
        {
            return new ClearCartResponse { Success = true };
        }

        // Tüm item'ları sil
        _dbContext.CartItems.RemoveRange(cart.Items);

        // Cart totals'ı sıfırla
        cart.Subtotal = 0;
        cart.Tax = 0;
        cart.Shipping = 0;
        cart.Discount = 0;
        cart.Total = 0;
        cart.LastUpdatedAt = DateTime.UtcNow;

        await _dbContext.SaveChangesAsync(cancellationToken);

        return new ClearCartResponse { Success = true };
    }
}

