using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Infrastructure.Persistence;
using Finbuckle.MultiTenant;

namespace Tinisoft.Application.Discounts.Queries.GetCouponStatistics;

public class GetCouponStatisticsQueryHandler : IRequestHandler<GetCouponStatisticsQuery, GetCouponStatisticsResponse>
{
    private readonly ApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly ILogger<GetCouponStatisticsQueryHandler> _logger;

    public GetCouponStatisticsQueryHandler(
        ApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor,
        ILogger<GetCouponStatisticsQueryHandler> logger)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
        _logger = logger;
    }

    public async Task<GetCouponStatisticsResponse> Handle(GetCouponStatisticsQuery request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        // Kuponu kontrol et
        var coupon = await _dbContext.Coupons
            .AsNoTracking()
            .FirstOrDefaultAsync(c => c.Id == request.CouponId && c.TenantId == tenantId, cancellationToken);

        if (coupon == null)
        {
            throw new KeyNotFoundException($"Kupon bulunamadı: {request.CouponId}");
        }

        // Kupon kullanımlarını getir
        var usages = await _dbContext.CouponUsages
            .AsNoTracking()
            .Include(cu => cu.Order)
            .Include(cu => cu.Customer)
            .Where(cu => cu.CouponId == request.CouponId && cu.TenantId == tenantId)
            .OrderByDescending(cu => cu.UsedAt)
            .ToListAsync(cancellationToken);

        var totalUsageCount = usages.Count;
        var uniqueCustomerCount = usages.Where(u => u.CustomerId.HasValue).Select(u => u.CustomerId.Value).Distinct().Count();
        var totalDiscountAmount = usages.Sum(u => u.DiscountAmount);
        var averageDiscountAmount = totalUsageCount > 0 ? totalDiscountAmount / totalUsageCount : 0;
        var firstUsedAt = usages.OrderBy(u => u.UsedAt).FirstOrDefault()?.UsedAt;
        var lastUsedAt = usages.OrderByDescending(u => u.UsedAt).FirstOrDefault()?.UsedAt;

        // Son 10 kullanım
        var recentUsages = usages.Take(10).Select(u => new CouponUsageDetailDto
        {
            OrderId = u.OrderId,
            OrderNumber = u.Order?.OrderNumber ?? "",
            CustomerId = u.CustomerId,
            CustomerEmail = u.Customer?.Email,
            DiscountAmount = u.DiscountAmount,
            OrderTotal = 0, // Order'dan alınabilir (TotalsJson'dan parse edilebilir)
            UsedAt = u.UsedAt
        }).ToList();

        return new GetCouponStatisticsResponse
        {
            CouponId = coupon.Id,
            Code = coupon.Code,
            Name = coupon.Name,
            TotalUsageCount = totalUsageCount,
            UniqueCustomerCount = uniqueCustomerCount,
            TotalDiscountAmount = Math.Round(totalDiscountAmount, 2, MidpointRounding.AwayFromZero),
            AverageDiscountAmount = Math.Round(averageDiscountAmount, 2, MidpointRounding.AwayFromZero),
            FirstUsedAt = firstUsedAt,
            LastUsedAt = lastUsedAt,
            RecentUsages = recentUsages
        };
    }
}

