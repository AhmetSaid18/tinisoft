using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Application.Common.Interfaces;
using Tinisoft.Shared.Contracts;
using Finbuckle.MultiTenant;

namespace Tinisoft.Application.Discounts.Commands.DeleteCoupon;

public class DeleteCouponCommandHandler : IRequestHandler<DeleteCouponCommand, DeleteCouponResponse>
{
    private readonly IApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly ILogger<DeleteCouponCommandHandler> _logger;

    public DeleteCouponCommandHandler(
        IApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor,
        ILogger<DeleteCouponCommandHandler> logger)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
        _logger = logger;
    }

    public async Task<DeleteCouponResponse> Handle(DeleteCouponCommand request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        var coupon = await _dbContext.Coupons
            .FirstOrDefaultAsync(c => c.Id == request.CouponId && c.TenantId == tenantId, cancellationToken);

        if (coupon == null)
        {
            throw new KeyNotFoundException($"Kupon bulunamadı: {request.CouponId}");
        }

        // Kupon kullanılmışsa silme, sadece pasif yap
        if (coupon.UsageCount > 0)
        {
            coupon.IsActive = false;
            _logger.LogWarning("Coupon {Code} has been used, deactivating instead of deleting", coupon.Code);
        }
        else
        {
            _dbContext.Coupons.Remove(coupon);
        }

        await _dbContext.SaveChangesAsync(cancellationToken);

        return new DeleteCouponResponse { Success = true };
    }
}



