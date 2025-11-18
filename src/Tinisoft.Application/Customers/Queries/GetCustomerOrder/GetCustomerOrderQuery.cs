using MediatR;

namespace Tinisoft.Application.Customers.Queries.GetCustomerOrder;

/// <summary>
/// Müşterinin sipariş detayı (sadece kendi siparişini görebilir)
/// </summary>
public class GetCustomerOrderQuery : IRequest<GetCustomerOrderResponse>
{
    public Guid OrderId { get; set; }
}

public class GetCustomerOrderResponse
{
    public Guid Id { get; set; }
    public string OrderNumber { get; set; } = string.Empty;
    public string Status { get; set; } = string.Empty;
    
    // Customer Info
    public string CustomerEmail { get; set; } = string.Empty;
    public string? CustomerPhone { get; set; }
    public string? CustomerFirstName { get; set; }
    public string? CustomerLastName { get; set; }
    
    // Shipping Address
    public ShippingAddressDto ShippingAddress { get; set; } = new();
    
    // Totals
    public OrderTotalsDto Totals { get; set; } = new();
    
    // Payment
    public string? PaymentStatus { get; set; }
    public string? PaymentProvider { get; set; }
    public DateTime? PaidAt { get; set; }
    
    // Shipping
    public string? ShippingMethod { get; set; }
    public string? TrackingNumber { get; set; }
    
    // Items
    public List<OrderItemDto> Items { get; set; } = new();
    
    public DateTime CreatedAt { get; set; }
    public DateTime? UpdatedAt { get; set; }
}

public class ShippingAddressDto
{
    public string? AddressLine1 { get; set; }
    public string? AddressLine2 { get; set; }
    public string? City { get; set; }
    public string? State { get; set; }
    public string? PostalCode { get; set; }
    public string? Country { get; set; }
}

public class OrderTotalsDto
{
    public decimal Subtotal { get; set; }
    public decimal Tax { get; set; }
    public decimal Shipping { get; set; }
    public decimal Discount { get; set; }
    public decimal Total { get; set; }
}

public class OrderItemDto
{
    public Guid Id { get; set; }
    public Guid ProductId { get; set; }
    public Guid? ProductVariantId { get; set; }
    public string Title { get; set; } = string.Empty;
    public string? SKU { get; set; }
    public int Quantity { get; set; }
    public decimal UnitPrice { get; set; }
    public decimal TotalPrice { get; set; }
}

