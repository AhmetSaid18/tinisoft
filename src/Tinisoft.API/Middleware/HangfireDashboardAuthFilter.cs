using Hangfire.Dashboard;

namespace Tinisoft.API.Middleware;

/// <summary>
/// Hangfire Dashboard için authentication filter
/// Production'da sadece admin kullanıcıların erişmesini sağlar
/// </summary>
public class HangfireDashboardAuthFilter : IDashboardAuthorizationFilter
{
    public bool Authorize(DashboardContext context)
    {
        var httpContext = context.GetHttpContext();
        
        // Development ortamında herkese izin ver
        var env = httpContext.RequestServices.GetRequiredService<IHostEnvironment>();
        if (env.IsDevelopment())
        {
            return true;
        }
        
        // JWT token kontrolü - Header'dan veya Cookie'den al
        var token = httpContext.Request.Headers["Authorization"].FirstOrDefault()?.Split(" ").Last()
                    ?? httpContext.Request.Cookies["jwt"];
        
        if (string.IsNullOrEmpty(token))
        {
            return false;
        }
        
        // Token'dan role claim'ini kontrol et (basit check)
        // Daha güvenli implementasyon için IJwtTokenService inject edilebilir
        try
        {
            var handler = new System.IdentityModel.Tokens.Jwt.JwtSecurityTokenHandler();
            var jwtToken = handler.ReadJwtToken(token);
            
            var roleClaim = jwtToken.Claims.FirstOrDefault(c => c.Type == "role" || c.Type == "roles");
            if (roleClaim != null && (roleClaim.Value == "SuperAdmin" || roleClaim.Value == "Admin"))
            {
                return true;
            }
        }
        catch
        {
            // Token parse edilemezse erişimi engelle
            return false;
        }
        
        return false;
    }
}

