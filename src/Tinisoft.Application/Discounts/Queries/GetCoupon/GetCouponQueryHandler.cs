using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Application.Common.Interfaces;
using Tinisoft.Shared.Contracts;
using Finbuckle.MultiTenant;

namespace Tinisoft.Application.Discounts.Queries.GetCoupon;

public class GetCouponQueryHandler : IRequestHandler<GetCouponQuery, GetCouponResponse>
{
    private readonly IApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly ILogger<GetCouponQueryHandler> _logger;

    public GetCouponQueryHandler(
        IApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor,
        ILogger<GetCouponQueryHandler> logger)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
        _logger = logger;
    }

    public async Task<GetCouponResponse> Handle(GetCouponQuery request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        var coupon = await _dbContext.Coupons
            .AsNoTracking()
            .Include(c => c.ApplicableProducts)
            .Include(c => c.ApplicableCategories)
            .Include(c => c.ExcludedProducts)
            .Include(c => c.ApplicableCustomers)
            
            .FirstOrDefaultAsync(c => c.Id == request.CouponId && c.TenantId == tenantId, cancellationToken);

        if (coupon == null)
        {
            throw new KeyNotFoundException($"Kupon bulunamadı: {request.CouponId}");
        }

        return new GetCouponResponse
        {
            Id = coupon.Id,
            Code = coupon.Code,
            Name = coupon.Name,
            Description = coupon.Description,
            DiscountType = coupon.DiscountType,
            DiscountValue = coupon.DiscountValue,
            Currency = coupon.Currency,
            MinOrderAmount = coupon.MinOrderAmount,
            MaxDiscountAmount = coupon.MaxDiscountAmount,
            MaxUsageCount = coupon.MaxUsageCount,
            MaxUsagePerCustomer = coupon.MaxUsagePerCustomer,
            ValidFrom = coupon.ValidFrom,
            ValidTo = coupon.ValidTo,
            AppliesToAllProducts = coupon.AppliesToAllProducts,
            ApplicableProductIds = coupon.ApplicableProducts.Select(cp => cp.ProductId).ToList(),
            ApplicableCategoryIds = coupon.ApplicableCategories.Select(cc => cc.CategoryId).ToList(),
            ExcludedProductIds = coupon.ExcludedProducts.Select(cep => cep.ProductId).ToList(),
            AppliesToAllCustomers = coupon.AppliesToAllCustomers,
            ApplicableCustomerIds = coupon.ApplicableCustomers.Select(cc => cc.CustomerId).ToList(),
            IsActive = coupon.IsActive,
            UsageCount = coupon.UsageCount,
            CreatedAt = coupon.CreatedAt,
            UpdatedAt = coupon.UpdatedAt
        };
    }
}



