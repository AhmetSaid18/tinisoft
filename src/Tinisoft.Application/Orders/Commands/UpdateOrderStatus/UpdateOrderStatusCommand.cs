using MediatR;

namespace Tinisoft.Application.Orders.Commands.UpdateOrderStatus;

public class UpdateOrderStatusCommand : IRequest<UpdateOrderStatusResponse>
{
    public Guid OrderId { get; set; }
    public string Status { get; set; } = string.Empty; // Pending, Paid, Processing, Shipped, Delivered, Cancelled
    public string? TrackingNumber { get; set; }
}

public class UpdateOrderStatusResponse
{
    public Guid OrderId { get; set; }
    public string Status { get; set; } = string.Empty;
}



