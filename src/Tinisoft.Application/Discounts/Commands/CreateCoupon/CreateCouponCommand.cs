using MediatR;

namespace Tinisoft.Application.Discounts.Commands.CreateCoupon;

/// <summary>
/// Kupon oluştur (TenantAdmin için)
/// </summary>
public class CreateCouponCommand : IRequest<CreateCouponResponse>
{
    public string Code { get; set; } = string.Empty;
    public string Name { get; set; } = string.Empty;
    public string? Description { get; set; }
    public string DiscountType { get; set; } = "Percentage"; // Percentage, FixedAmount, FreeShipping
    public decimal DiscountValue { get; set; }
    public string Currency { get; set; } = "TRY";
    public decimal? MinOrderAmount { get; set; }
    public decimal? MaxDiscountAmount { get; set; }
    public int? MaxUsageCount { get; set; }
    public int? MaxUsagePerCustomer { get; set; }
    public DateTime? ValidFrom { get; set; }
    public DateTime? ValidTo { get; set; }
    public bool AppliesToAllProducts { get; set; } = true;
    public List<Guid>? ApplicableProductIds { get; set; }
    public List<Guid>? ApplicableCategoryIds { get; set; }
    public List<Guid>? ExcludedProductIds { get; set; }
    public bool AppliesToAllCustomers { get; set; } = true;
    public List<Guid>? ApplicableCustomerIds { get; set; }
}

public class CreateCouponResponse
{
    public Guid CouponId { get; set; }
    public string Code { get; set; } = string.Empty;
}



