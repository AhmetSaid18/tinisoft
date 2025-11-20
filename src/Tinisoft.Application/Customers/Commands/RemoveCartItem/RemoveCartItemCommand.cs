using MediatR;

namespace Tinisoft.Application.Customers.Commands.RemoveCartItem;

public class RemoveCartItemCommand : IRequest<RemoveCartItemResponse>
{
    public Guid CartItemId { get; set; }
}

public class RemoveCartItemResponse
{
    public bool Success { get; set; }
    public decimal CartTotal { get; set; }
}



