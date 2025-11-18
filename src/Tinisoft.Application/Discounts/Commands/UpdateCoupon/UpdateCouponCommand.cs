using MediatR;

namespace Tinisoft.Application.Discounts.Commands.UpdateCoupon;

public class UpdateCouponCommand : IRequest<UpdateCouponResponse>
{
    public Guid CouponId { get; set; }
    public string? Name { get; set; }
    public string? Description { get; set; }
    public string? DiscountType { get; set; }
    public decimal? DiscountValue { get; set; }
    public string? Currency { get; set; }
    public decimal? MinOrderAmount { get; set; }
    public decimal? MaxDiscountAmount { get; set; }
    public int? MaxUsageCount { get; set; }
    public int? MaxUsagePerCustomer { get; set; }
    public DateTime? ValidFrom { get; set; }
    public DateTime? ValidTo { get; set; }
    public bool? IsActive { get; set; }
}

public class UpdateCouponResponse
{
    public Guid CouponId { get; set; }
    public bool Success { get; set; }
}

