using MediatR;

namespace Tinisoft.Application.Customers.Commands.ApplyCouponToCart;

/// <summary>
/// Sepete kupon uygula
/// </summary>
public class ApplyCouponToCartCommand : IRequest<ApplyCouponToCartResponse>
{
    public string CouponCode { get; set; } = string.Empty;
}

public class ApplyCouponToCartResponse
{
    public bool Success { get; set; }
    public string? ErrorMessage { get; set; }
    public string? CouponCode { get; set; }
    public string? CouponName { get; set; }
    public decimal DiscountAmount { get; set; }
    public decimal CartTotal { get; set; }
}



