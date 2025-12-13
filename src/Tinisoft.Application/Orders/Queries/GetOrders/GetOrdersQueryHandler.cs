using MediatR;
using System.Text.Json;
using Finbuckle.MultiTenant;

namespace Tinisoft.Application.Orders.Queries.GetOrders;

public class GetOrdersQueryHandler : IRequestHandler<GetOrdersQuery, PagedOrdersResponse>
{
    private readonly IApplicationDbContext _context;
    private readonly IMultiTenantContextAccessor _tenantAccessor;

    public GetOrdersQueryHandler(IApplicationDbContext context, IMultiTenantContextAccessor tenantAccessor)
    {
        _context = context;
        _tenantAccessor = tenantAccessor;
    }

    public async Task<PagedOrdersResponse> Handle(GetOrdersQuery request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        var query = _context.Orders
            .Where(o => o.TenantId == tenantId)
            .AsQueryable();

        // Filter by status
        if (!string.IsNullOrEmpty(request.Status))
        {
            query = query.Where(o => o.Status == request.Status);
        }

        // Filter by date range
        if (request.StartDate.HasValue)
        {
            query = query.Where(o => o.CreatedAt >= request.StartDate.Value);
        }

        if (request.EndDate.HasValue)
        {
            query = query.Where(o => o.CreatedAt <= request.EndDate.Value);
        }

        // Search
        if (!string.IsNullOrEmpty(request.Search))
        {
            var searchLower = request.Search.ToLower();
            query = query.Where(o => 
                o.OrderNumber.ToLower().Contains(searchLower) ||
                o.CustomerEmail.ToLower().Contains(searchLower) ||
                (o.CustomerFirstName != null && o.CustomerFirstName.ToLower().Contains(searchLower)) ||
                (o.CustomerLastName != null && o.CustomerLastName.ToLower().Contains(searchLower)));
        }

        // Get total count
        var totalCount = await query.CountAsync(cancellationToken);

        // Get paginated results
        var orders = await query
            .OrderByDescending(o => o.CreatedAt)
            .Skip((request.Page - 1) * request.PageSize)
            .Take(request.PageSize)
            .Select(o => new OrderSummary
            {
                Id = o.Id,
                OrderNumber = o.OrderNumber,
                Status = o.Status,
                CustomerEmail = o.CustomerEmail,
                CustomerName = o.CustomerFirstName != null && o.CustomerLastName != null 
                    ? $"{o.CustomerFirstName} {o.CustomerLastName}" 
                    : null,
                Total = 0, // Will be set from JSON
                PaymentStatus = o.PaymentStatus,
                CreatedAt = o.CreatedAt
            })
            .ToListAsync(cancellationToken);

        // Parse totals from JSON (can't do in LINQ to SQL)
        var orderIds = orders.Select(o => o.Id).ToList();
        var orderTotals = await _context.Orders
            .Where(o => orderIds.Contains(o.Id))
            .Select(o => new { o.Id, o.TotalsJson })
            .ToListAsync(cancellationToken);

        foreach (var order in orders)
        {
            var totalsJson = orderTotals.FirstOrDefault(ot => ot.Id == order.Id)?.TotalsJson ?? "{}";
            try
            {
                var totals = JsonSerializer.Deserialize<Dictionary<string, decimal>>(totalsJson);
                order.Total = totals?.GetValueOrDefault("total", 0) ?? 0;
            }
            catch
            {
                order.Total = 0;
            }
        }

        return new PagedOrdersResponse
        {
            Items = orders,
            TotalCount = totalCount,
            TotalPages = (int)Math.Ceiling(totalCount / (double)request.PageSize),
            CurrentPage = request.Page
        };
    }
}

