using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Domain.Entities;
using Tinisoft.Domain.Common;
using Tinisoft.Application.Common.Interfaces;
using Tinisoft.Shared.Contracts;

namespace Tinisoft.Application.Admin.Queries.GetSystemStatistics;

public class GetSystemStatisticsQueryHandler : IRequestHandler<GetSystemStatisticsQuery, GetSystemStatisticsResponse>
{
    private readonly IApplicationDbContext _dbContext;
    private readonly ILogger<GetSystemStatisticsQueryHandler> _logger;

    public GetSystemStatisticsQueryHandler(
        IApplicationDbContext dbContext,
        ILogger<GetSystemStatisticsQueryHandler> logger)
    {
        _dbContext = dbContext;
        _logger = logger;
    }

    public async Task<GetSystemStatisticsResponse> Handle(GetSystemStatisticsQuery request, CancellationToken cancellationToken)
    {
        var totalUsers = await _dbContext.Set<User>().CountAsync(cancellationToken);
        var totalTenants = await _dbContext.Set<Entities.Tenant>().CountAsync(cancellationToken);
        var activeTenants = await _dbContext.Set<Entities.Tenant>().CountAsync(t => t.IsActive, cancellationToken);
        var totalProducts = await _dbContext.Set<Product>().CountAsync(cancellationToken);
        var totalOrders = await _dbContext.Set<Order>().CountAsync(cancellationToken);

        // Revenue hesaplama (Order'ların toplam tutarı - TotalsJson'dan total değerini al)
        var completedOrders = await _dbContext.Set<Order>()
            .Where(o => o.Status == "Completed" || o.Status == "Delivered")
            .ToListAsync(cancellationToken);

        var totalRevenue = completedOrders
            .Select(o => ExtractTotalFromJson(o.TotalsJson))
            .Sum();

        var startOfMonth = new DateTime(DateTime.UtcNow.Year, DateTime.UtcNow.Month, 1);
        var monthlyOrders = await _dbContext.Set<Order>()
            .Where(o => o.CreatedAt >= startOfMonth && (o.Status == "Completed" || o.Status == "Delivered"))
            .ToListAsync(cancellationToken);

        var monthlyRevenue = monthlyOrders
            .Select(o => ExtractTotalFromJson(o.TotalsJson))
            .Sum();

        // Role bazlı kullanıcı sayıları
        var systemAdminCount = await _dbContext.Set<User>()
            .CountAsync(u => u.SystemRole == Roles.SystemAdmin, cancellationToken);
        var tenantAdminCount = await _dbContext.Set<User>()
            .CountAsync(u => u.SystemRole == Roles.TenantAdmin, cancellationToken);
        var customerCount = await _dbContext.Set<User>()
            .CountAsync(u => u.SystemRole == Roles.Customer, cancellationToken);

        return new GetSystemStatisticsResponse
        {
            TotalUsers = totalUsers,
            TotalTenants = totalTenants,
            ActiveTenants = activeTenants,
            TotalProducts = totalProducts,
            TotalOrders = totalOrders,
            TotalRevenue = totalRevenue,
            MonthlyRevenue = monthlyRevenue,
            SystemAdminCount = systemAdminCount,
            TenantAdminCount = tenantAdminCount,
            CustomerCount = customerCount
        };
    }

    private static decimal ExtractTotalFromJson(string totalsJson)
    {
        try
        {
            using var doc = System.Text.Json.JsonDocument.Parse(totalsJson);
            if (doc.RootElement.TryGetProperty("total", out var totalElement))
            {
                return totalElement.GetDecimal();
            }
        }
        catch
        {
            // JSON parse hatası durumunda 0 döndür
        }
        return 0;
    }
}



