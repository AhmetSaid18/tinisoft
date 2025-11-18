using MediatR;

namespace Tinisoft.Application.Discounts.Commands.DeleteCoupon;

public class DeleteCouponCommand : IRequest<DeleteCouponResponse>
{
    public Guid CouponId { get; set; }
}

public class DeleteCouponResponse
{
    public bool Success { get; set; }
}

