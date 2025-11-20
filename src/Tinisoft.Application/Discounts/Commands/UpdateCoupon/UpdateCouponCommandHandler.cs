using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Application.Common.Interfaces;
using Tinisoft.Shared.Contracts;
using Finbuckle.MultiTenant;

namespace Tinisoft.Application.Discounts.Commands.UpdateCoupon;

public class UpdateCouponCommandHandler : IRequestHandler<UpdateCouponCommand, UpdateCouponResponse>
{
    private readonly IApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly ILogger<UpdateCouponCommandHandler> _logger;

    public UpdateCouponCommandHandler(
        IApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor,
        ILogger<UpdateCouponCommandHandler> logger)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
        _logger = logger;
    }

    public async Task<UpdateCouponResponse> Handle(UpdateCouponCommand request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        var coupon = await _dbContext.Coupons
            .FirstOrDefaultAsync(c => c.Id == request.CouponId && c.TenantId == tenantId, cancellationToken);

        if (coupon == null)
        {
            throw new KeyNotFoundException($"Kupon bulunamadı: {request.CouponId}");
        }

        // Update fields (sadece null olmayanlar)
        if (request.Name != null) coupon.Name = request.Name;
        if (request.Description != null) coupon.Description = request.Description;
        if (request.DiscountType != null) coupon.DiscountType = request.DiscountType;
        if (request.DiscountValue.HasValue) coupon.DiscountValue = request.DiscountValue.Value;
        if (request.Currency != null) coupon.Currency = request.Currency;
        if (request.MinOrderAmount.HasValue) coupon.MinOrderAmount = request.MinOrderAmount;
        if (request.MaxDiscountAmount.HasValue) coupon.MaxDiscountAmount = request.MaxDiscountAmount;
        if (request.MaxUsageCount.HasValue) coupon.MaxUsageCount = request.MaxUsageCount;
        if (request.MaxUsagePerCustomer.HasValue) coupon.MaxUsagePerCustomer = request.MaxUsagePerCustomer;
        if (request.ValidFrom.HasValue) coupon.ValidFrom = request.ValidFrom;
        if (request.ValidTo.HasValue) coupon.ValidTo = request.ValidTo;
        if (request.IsActive.HasValue) coupon.IsActive = request.IsActive.Value;

        await _dbContext.SaveChangesAsync(cancellationToken);

        _logger.LogInformation("Coupon updated: {Code}", coupon.Code);

        return new UpdateCouponResponse
        {
            CouponId = coupon.Id,
            Success = true
        };
    }
}



