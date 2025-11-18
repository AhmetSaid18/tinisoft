using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Infrastructure.Persistence;
using Tinisoft.Application.Common.Interfaces;
using Finbuckle.MultiTenant;

namespace Tinisoft.Application.Customers.Commands.RemoveCartItem;

public class RemoveCartItemCommandHandler : IRequestHandler<RemoveCartItemCommand, RemoveCartItemResponse>
{
    private readonly ApplicationDbContext _dbContext;
    private readonly ICurrentCustomerService _currentCustomerService;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly ILogger<RemoveCartItemCommandHandler> _logger;

    public RemoveCartItemCommandHandler(
        ApplicationDbContext dbContext,
        ICurrentCustomerService currentCustomerService,
        IMultiTenantContextAccessor tenantAccessor,
        ILogger<RemoveCartItemCommandHandler> logger)
    {
        _dbContext = dbContext;
        _currentCustomerService = currentCustomerService;
        _tenantAccessor = tenantAccessor;
        _logger = logger;
    }

    public async Task<RemoveCartItemResponse> Handle(RemoveCartItemCommand request, CancellationToken cancellationToken)
    {
        var customerId = _currentCustomerService.GetCurrentCustomerId();
        if (!customerId.HasValue)
        {
            throw new UnauthorizedAccessException("Müşteri bilgisi bulunamadı");
        }

        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        // CartItem'ı getir
        var cartItem = await _dbContext.CartItems
            .Include(ci => ci.Cart)
            .FirstOrDefaultAsync(ci => ci.Id == request.CartItemId && 
                ci.Cart.TenantId == tenantId && 
                ci.Cart.CustomerId == customerId.Value, cancellationToken);

        if (cartItem == null)
        {
            throw new KeyNotFoundException("Sepet öğesi bulunamadı");
        }

        var cart = cartItem.Cart;

        // Item'ı sil
        _dbContext.CartItems.Remove(cartItem);

        // Cart totals'ı güncelle
        cart.Subtotal = cart.Items.Where(ci => ci.Id != cartItem.Id).Sum(ci => ci.TotalPrice);
        cart.Tax = 0;
        cart.Shipping = 0;
        cart.Discount = 0;
        cart.Total = cart.Subtotal + cart.Tax + cart.Shipping - cart.Discount;
        cart.LastUpdatedAt = DateTime.UtcNow;

        await _dbContext.SaveChangesAsync(cancellationToken);

        return new RemoveCartItemResponse
        {
            Success = true,
            CartTotal = cart.Total
        };
    }
}

