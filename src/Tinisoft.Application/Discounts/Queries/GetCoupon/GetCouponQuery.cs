using MediatR;

namespace Tinisoft.Application.Discounts.Queries.GetCoupon;

/// <summary>
/// Kupon detayı (TenantAdmin için)
/// </summary>
public class GetCouponQuery : IRequest<GetCouponResponse>
{
    public Guid CouponId { get; set; }
}

public class GetCouponResponse
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
    public bool AppliesToAllProducts { get; set; }
    public List<Guid> ApplicableProductIds { get; set; } = new();
    public List<Guid> ApplicableCategoryIds { get; set; } = new();
    public List<Guid> ExcludedProductIds { get; set; } = new();
    public bool AppliesToAllCustomers { get; set; }
    public List<Guid> ApplicableCustomerIds { get; set; } = new();
    public bool IsActive { get; set; }
    public int UsageCount { get; set; }
    public DateTime CreatedAt { get; set; }
    public DateTime? UpdatedAt { get; set; }
}

