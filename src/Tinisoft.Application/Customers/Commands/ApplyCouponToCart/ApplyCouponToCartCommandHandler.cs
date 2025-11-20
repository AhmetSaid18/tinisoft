using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Application.Common.Interfaces;
using Tinisoft.Shared.Contracts;
using Tinisoft.Application.Common.Interfaces;
using Tinisoft.Application.Discounts.Services;
using Finbuckle.MultiTenant;

namespace Tinisoft.Application.Customers.Commands.ApplyCouponToCart;

public class ApplyCouponToCartCommandHandler : IRequestHandler<ApplyCouponToCartCommand, ApplyCouponToCartResponse>
{
    private readonly IApplicationDbContext _dbContext;
    private readonly ICurrentCustomerService _currentCustomerService;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly ICouponValidationService _couponValidationService;
    private readonly ILogger<ApplyCouponToCartCommandHandler> _logger;

    public ApplyCouponToCartCommandHandler(
        IApplicationDbContext dbContext,
        ICurrentCustomerService currentCustomerService,
        IMultiTenantContextAccessor tenantAccessor,
        ICouponValidationService couponValidationService,
        ILogger<ApplyCouponToCartCommandHandler> logger)
    {
        _dbContext = dbContext;
        _currentCustomerService = currentCustomerService;
        _tenantAccessor = tenantAccessor;
        _couponValidationService = couponValidationService;
        _logger = logger;
    }

    public async Task<ApplyCouponToCartResponse> Handle(ApplyCouponToCartCommand request, CancellationToken cancellationToken)
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
                .ThenInclude(ci => ci.Product)
                    .ThenInclude(p => p.ProductCategories)
                        .ThenInclude(pc => pc.Category)
            
            .FirstOrDefaultAsync(c => c.TenantId == tenantId && c.CustomerId == customerId.Value, cancellationToken);

        if (cart == null || !cart.Items.Any())
        {
            return new ApplyCouponToCartResponse
            {
                Success = false,
                ErrorMessage = "Sepet boş"
            };
        }

        // Product ve Category ID'lerini topla
        var productIds = cart.Items.Select(ci => ci.ProductId).ToList();
        var categoryIds = cart.Items
            .SelectMany(ci => ci.Product?.ProductCategories?.Select(pc => pc.CategoryId) ?? Enumerable.Empty<Guid>())
            .Distinct()
            .ToList();

        // Kuponu doğrula
        var validationResult = await _couponValidationService.ValidateCouponAsync(
            request.CouponCode,
            customerId.Value,
            cart.Subtotal,
            productIds,
            categoryIds,
            cancellationToken);

        if (!validationResult.IsValid)
        {
            return new ApplyCouponToCartResponse
            {
                Success = false,
                ErrorMessage = validationResult.ErrorMessage
            };
        }

        // Cart items'ı indirim hesaplaması için hazırla
        var cartItemsForDiscount = cart.Items.Select(ci => new Tinisoft.Application.Discounts.Services.CartItemForDiscount
        {
            ProductId = ci.ProductId,
            CategoryIds = ci.Product?.ProductCategories?.Select(pc => pc.CategoryId).ToList() ?? new List<Guid>(),
            TotalPrice = ci.TotalPrice
        }).ToList();

        // Ürün/kategori bazlı indirim hesapla
        var discountAmount = _couponValidationService.CalculateDiscount(validationResult.Coupon!, cartItemsForDiscount);

        // Kuponu sepete uygula
        cart.CouponCode = validationResult.Coupon!.Code;
        cart.CouponId = validationResult.Coupon.Id;
        cart.Discount = discountAmount;
        cart.Total = cart.Subtotal + cart.Tax + cart.Shipping - cart.Discount;
        cart.LastUpdatedAt = DateTime.UtcNow;

        await _dbContext.SaveChangesAsync(cancellationToken);

        return new ApplyCouponToCartResponse
        {
            Success = true,
            CouponCode = validationResult.Coupon.Code,
            CouponName = validationResult.Coupon.Name,
            DiscountAmount = validationResult.DiscountAmount,
            CartTotal = cart.Total
        };
    }
}



