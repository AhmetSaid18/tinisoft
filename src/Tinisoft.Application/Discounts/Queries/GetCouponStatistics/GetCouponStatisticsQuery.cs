using MediatR;

namespace Tinisoft.Application.Discounts.Queries.GetCouponStatistics;

/// <summary>
/// Kupon istatistikleri (TenantAdmin için)
/// </summary>
public class GetCouponStatisticsQuery : IRequest<GetCouponStatisticsResponse>
{
    public Guid CouponId { get; set; }
}

public class GetCouponStatisticsResponse
{
    public Guid CouponId { get; set; }
    public string Code { get; set; } = string.Empty;
    public string Name { get; set; } = string.Empty;
    public int TotalUsageCount { get; set; }
    public int UniqueCustomerCount { get; set; }
    public decimal TotalDiscountAmount { get; set; }
    public decimal AverageDiscountAmount { get; set; }
    public DateTime? FirstUsedAt { get; set; }
    public DateTime? LastUsedAt { get; set; }
    public List<CouponUsageDetailDto> RecentUsages { get; set; } = new();
}

public class CouponUsageDetailDto
{
    public Guid OrderId { get; set; }
    public string OrderNumber { get; set; } = string.Empty;
    public Guid? CustomerId { get; set; }
    public string? CustomerEmail { get; set; }
    public decimal DiscountAmount { get; set; }
    public decimal OrderTotal { get; set; }
    public DateTime UsedAt { get; set; }
}



