using MediatR;

namespace Tinisoft.Application.Customers.Queries.GetCustomerOrders;

/// <summary>
/// Müşterinin siparişlerini listele
/// </summary>
public class GetCustomerOrdersQuery : IRequest<GetCustomerOrdersResponse>
{
    public int Page { get; set; } = 1;
    public int PageSize { get; set; } = 20;
    public string? Status { get; set; } // Filter by status (Pending, Paid, Processing, Shipped, Delivered, Cancelled)
}

public class GetCustomerOrdersResponse
{
    public List<CustomerOrderDto> Orders { get; set; } = new();
    public int TotalCount { get; set; }
    public int Page { get; set; }
    public int PageSize { get; set; }
    public int TotalPages => (int)Math.Ceiling(TotalCount / (double)PageSize);
}

public class CustomerOrderDto
{
    public Guid Id { get; set; }
    public string OrderNumber { get; set; } = string.Empty;
    public string Status { get; set; } = string.Empty;
    public decimal Total { get; set; }
    public string Currency { get; set; } = "TRY";
    public string? PaymentStatus { get; set; }
    public string? ShippingMethod { get; set; }
    public string? TrackingNumber { get; set; }
    public DateTime CreatedAt { get; set; }
    public int ItemCount { get; set; } // Toplam ürün sayısı
}

