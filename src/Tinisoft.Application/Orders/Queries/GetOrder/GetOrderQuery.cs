using MediatR;

namespace Tinisoft.Application.Orders.Queries.GetOrder;

public class GetOrderQuery : IRequest<GetOrderResponse>
{
    public Guid OrderId { get; set; }
}

public class GetOrderResponse
{
    public Guid Id { get; set; }
    public string OrderNumber { get; set; } = string.Empty;
    public string Status { get; set; } = string.Empty;
    public string CustomerEmail { get; set; } = string.Empty;
    public string? CustomerPhone { get; set; }
    public string? CustomerFirstName { get; set; }
    public string? CustomerLastName { get; set; }
    public OrderTotalsDto Totals { get; set; } = new();
    public string? PaymentStatus { get; set; }
    public string? PaymentProvider { get; set; }
    public DateTime? PaidAt { get; set; }
    public string? ShippingMethod { get; set; }
    public string? TrackingNumber { get; set; }
    public DateTime CreatedAt { get; set; }
    public List<OrderItemResponse> Items { get; set; } = new();
}

public class OrderTotalsDto
{
    public decimal Subtotal { get; set; }
    public decimal Tax { get; set; }
    public decimal Shipping { get; set; }
    public decimal Discount { get; set; }
    public decimal Total { get; set; }
}

public class OrderItemResponse
{
    public Guid Id { get; set; }
    public Guid ProductId { get; set; }
    public Guid? ProductVariantId { get; set; }
    public string Title { get; set; } = string.Empty;
    public int Quantity { get; set; }
    public decimal UnitPrice { get; set; }
    public decimal TotalPrice { get; set; }
}

