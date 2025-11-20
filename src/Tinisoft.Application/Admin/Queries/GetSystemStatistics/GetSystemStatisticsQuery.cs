using MediatR;

namespace Tinisoft.Application.Admin.Queries.GetSystemStatistics;

public class GetSystemStatisticsQuery : IRequest<GetSystemStatisticsResponse>
{
}

public class GetSystemStatisticsResponse
{
    public int TotalUsers { get; set; }
    public int TotalTenants { get; set; }
    public int ActiveTenants { get; set; }
    public int TotalProducts { get; set; }
    public int TotalOrders { get; set; }
    public decimal TotalRevenue { get; set; }
    public decimal MonthlyRevenue { get; set; }
    public int SystemAdminCount { get; set; }
    public int TenantAdminCount { get; set; }
    public int CustomerCount { get; set; }
}



