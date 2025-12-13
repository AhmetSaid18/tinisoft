using MediatR;

namespace Tinisoft.Application.Orders.Queries.GetOrderStats;

public class GetOrderStatsQuery : IRequest<OrderStatsResponse>
{
    public DateTime StartDate { get; set; }
    public DateTime EndDate { get; set; }
}

public class OrderStatsResponse
{
    public int TotalOrders { get; set; }
    public int PendingOrders { get; set; }
    public int ProcessingOrders { get; set; }
    public int ShippedOrders { get; set; }
    public int DeliveredOrders { get; set; }
    public int CancelledOrders { get; set; }
    public decimal TotalRevenue { get; set; }
    public decimal AverageOrderValue { get; set; }
}

