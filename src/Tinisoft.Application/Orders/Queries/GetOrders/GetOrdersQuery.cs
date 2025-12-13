using MediatR;

namespace Tinisoft.Application.Orders.Queries.GetOrders;

public class GetOrdersQuery : IRequest<PagedOrdersResponse>
{
    public int Page { get; set; } = 1;
    public int PageSize { get; set; } = 20;
    public string? Status { get; set; }
    public string? Search { get; set; }
    public DateTime? StartDate { get; set; }
    public DateTime? EndDate { get; set; }
}

public class PagedOrdersResponse
{
    public List<OrderSummary> Items { get; set; } = new();
    public int TotalCount { get; set; }
    public int TotalPages { get; set; }
    public int CurrentPage { get; set; }
}

public class OrderSummary
{
    public Guid Id { get; set; }
    public string OrderNumber { get; set; } = string.Empty;
    public string Status { get; set; } = string.Empty;
    public string CustomerEmail { get; set; } = string.Empty;
    public string? CustomerName { get; set; }
    public decimal Total { get; set; }
    public string? PaymentStatus { get; set; }
    public DateTime CreatedAt { get; set; }
}

