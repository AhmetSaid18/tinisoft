using MediatR;

namespace Tinisoft.Application.Customers.Commands.RemoveCouponFromCart;

/// <summary>
/// Sepetten kuponu kaldır
/// </summary>
public class RemoveCouponFromCartCommand : IRequest<RemoveCouponFromCartResponse>
{
}

public class RemoveCouponFromCartResponse
{
    public bool Success { get; set; }
    public decimal CartTotal { get; set; }
}



