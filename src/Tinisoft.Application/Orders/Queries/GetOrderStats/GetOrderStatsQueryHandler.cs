using MediatR;
using System.Text.Json;
using Finbuckle.MultiTenant;

namespace Tinisoft.Application.Orders.Queries.GetOrderStats;

public class GetOrderStatsQueryHandler : IRequestHandler<GetOrderStatsQuery, OrderStatsResponse>
{
    private readonly IApplicationDbContext _context;
    private readonly IMultiTenantContextAccessor _tenantAccessor;

    public GetOrderStatsQueryHandler(IApplicationDbContext context, IMultiTenantContextAccessor tenantAccessor)
    {
        _context = context;
        _tenantAccessor = tenantAccessor;
    }

    public async Task<OrderStatsResponse> Handle(GetOrderStatsQuery request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        var orders = await _context.Orders
            .Where(o => o.TenantId == tenantId && 
                        o.CreatedAt >= request.StartDate && 
                        o.CreatedAt <= request.EndDate)
            .ToListAsync(cancellationToken);

        // Calculate totals from JSON
        decimal totalRevenue = 0;
        foreach (var order in orders.Where(o => o.PaymentStatus == "Paid"))
        {
            try
            {
                var totals = JsonSerializer.Deserialize<Dictionary<string, decimal>>(order.TotalsJson ?? "{}");
                totalRevenue += totals?.GetValueOrDefault("total", 0) ?? 0;
            }
            catch
            {
                // Skip invalid JSON
            }
        }

        var totalOrders = orders.Count;
        
        return new OrderStatsResponse
        {
            TotalOrders = totalOrders,
            PendingOrders = orders.Count(o => o.Status == "Pending"),
            ProcessingOrders = orders.Count(o => o.Status == "Processing"),
            ShippedOrders = orders.Count(o => o.Status == "Shipped"),
            DeliveredOrders = orders.Count(o => o.Status == "Delivered"),
            CancelledOrders = orders.Count(o => o.Status == "Cancelled"),
            TotalRevenue = totalRevenue,
            AverageOrderValue = totalOrders > 0 ? totalRevenue / totalOrders : 0
        };
    }
}

