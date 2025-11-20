using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Application.Common.Interfaces;
using Tinisoft.Shared.Contracts;
using Finbuckle.MultiTenant;

namespace Tinisoft.Application.Discounts.Commands.CreateCoupon;

public class CreateCouponCommandHandler : IRequestHandler<CreateCouponCommand, CreateCouponResponse>
{
    private readonly IApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly ILogger<CreateCouponCommandHandler> _logger;

    public CreateCouponCommandHandler(
        IApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor,
        ILogger<CreateCouponCommandHandler> logger)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
        _logger = logger;
    }

    public async Task<CreateCouponResponse> Handle(CreateCouponCommand request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        // Kupon kodu unique olmalı
        var existingCoupon = await _dbContext.Coupons
            .AnyAsync(c => c.TenantId == tenantId && c.Code.ToUpper() == request.Code.ToUpper(), cancellationToken);

        if (existingCoupon)
        {
            throw new InvalidOperationException($"Bu kupon kodu zaten kullanılıyor: {request.Code}");
        }

        var coupon = new Domain.Entities.Coupon
        {
            TenantId = tenantId,
            Code = request.Code.ToUpper(),
            Name = request.Name,
            Description = request.Description,
            DiscountType = request.DiscountType,
            DiscountValue = request.DiscountValue,
            Currency = request.Currency,
            MinOrderAmount = request.MinOrderAmount,
            MaxDiscountAmount = request.MaxDiscountAmount,
            MaxUsageCount = request.MaxUsageCount,
            MaxUsagePerCustomer = request.MaxUsagePerCustomer,
            ValidFrom = request.ValidFrom,
            ValidTo = request.ValidTo,
            AppliesToAllProducts = request.AppliesToAllProducts,
            AppliesToAllCustomers = request.AppliesToAllCustomers,
            IsActive = true,
            UsageCount = 0
        };

        _dbContext.Coupons.Add(coupon);
        await _dbContext.SaveChangesAsync(cancellationToken);

        // Applicable Products
        if (request.ApplicableProductIds != null && request.ApplicableProductIds.Any())
        {
            foreach (var productId in request.ApplicableProductIds)
            {
                _dbContext.CouponProducts.Add(new Domain.Entities.CouponProduct
                {
                    CouponId = coupon.Id,
                    ProductId = productId
                });
            }
        }

        // Applicable Categories
        if (request.ApplicableCategoryIds != null && request.ApplicableCategoryIds.Any())
        {
            foreach (var categoryId in request.ApplicableCategoryIds)
            {
                _dbContext.CouponCategories.Add(new Domain.Entities.CouponCategory
                {
                    CouponId = coupon.Id,
                    CategoryId = categoryId
                });
            }
        }

        // Excluded Products
        if (request.ExcludedProductIds != null && request.ExcludedProductIds.Any())
        {
            foreach (var productId in request.ExcludedProductIds)
            {
                _dbContext.CouponExcludedProducts.Add(new Domain.Entities.CouponExcludedProduct
                {
                    CouponId = coupon.Id,
                    ProductId = productId
                });
            }
        }

        // Applicable Customers
        if (request.ApplicableCustomerIds != null && request.ApplicableCustomerIds.Any())
        {
            foreach (var customerId in request.ApplicableCustomerIds)
            {
                _dbContext.CouponCustomers.Add(new Domain.Entities.CouponCustomer
                {
                    CouponId = coupon.Id,
                    CustomerId = customerId
                });
            }
        }

        await _dbContext.SaveChangesAsync(cancellationToken);

        _logger.LogInformation("Coupon created: {Code} - {Name}", coupon.Code, coupon.Name);

        return new CreateCouponResponse
        {
            CouponId = coupon.Id,
            Code = coupon.Code
        };
    }
}



