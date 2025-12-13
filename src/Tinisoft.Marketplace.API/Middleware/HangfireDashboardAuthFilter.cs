using Hangfire.Dashboard;

namespace Tinisoft.Marketplace.API.Middleware;

/// <summary>
/// Hangfire Dashboard için basit auth filter
/// Production'da daha güvenli bir authentication kullanılmalı
/// </summary>
public class HangfireDashboardAuthFilter : IDashboardAuthorizationFilter
{
    public bool Authorize(DashboardContext context)
    {
        // Development'da herkese izin ver
        // Production'da IP whitelist veya authentication eklenebilir
        return true;
    }
}

