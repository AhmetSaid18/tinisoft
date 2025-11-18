using MediatR;

namespace Tinisoft.Application.Discounts.Queries.GetCoupons;

/// <summary>
/// Kuponları listele (TenantAdmin için)
/// </summary>
public class GetCouponsQuery : IRequest<GetCouponsResponse>
{
    public int Page { get; set; } = 1;
    public int PageSize { get; set; } = 20;
    public bool? IsActive { get; set; }
    public string? Search { get; set; }
}

public class GetCouponsResponse
{
    public List<CouponDto> Coupons { get; set; } = new();
    public int TotalCount { get; set; }
    public int Page { get; set; }
    public int PageSize { get; set; }
    public int TotalPages => (int)Math.Ceiling(TotalCount / (double)PageSize);
}

public class CouponDto
{
    public Guid Id { get; set; }
    public string Code { get; set; } = string.Empty;
    public string Name { get; set; } = string.Empty;
    public string? Description { get; set; }
    public string DiscountType { get; set; } = string.Empty;
    public decimal DiscountValue { get; set; }
    public string Currency { get; set; } = "TRY";
    public decimal? MinOrderAmount { get; set; }
    public decimal? MaxDiscountAmount { get; set; }
    public int? MaxUsageCount { get; set; }
    public int? MaxUsagePerCustomer { get; set; }
    public DateTime? ValidFrom { get; set; }
    public DateTime? ValidTo { get; set; }
    public bool IsActive { get; set; }
    public int UsageCount { get; set; }
    public DateTime CreatedAt { get; set; }
}

