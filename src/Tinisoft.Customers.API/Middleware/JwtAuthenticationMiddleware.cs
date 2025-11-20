using Tinisoft.Customers.API.Attributes;
using Tinisoft.Application.Common.Interfaces;

namespace Tinisoft.Customers.API.Middleware;

public class JwtAuthenticationMiddleware
{
    private readonly RequestDelegate _next;
    private readonly IJwtTokenService _jwtTokenService;
    private readonly ILogger<JwtAuthenticationMiddleware> _logger;

    public JwtAuthenticationMiddleware(
        RequestDelegate next,
        IJwtTokenService jwtTokenService,
        ILogger<JwtAuthenticationMiddleware> logger)
    {
        _next = next;
        _jwtTokenService = jwtTokenService;
        _logger = logger;
    }

    public async Task InvokeAsync(HttpContext context)
    {
        var endpoint = context.GetEndpoint();
        if (endpoint != null)
        {
            var isPublic = endpoint.Metadata.GetMetadata<PublicAttribute>() != null;
            if (isPublic)
            {
                await _next(context);
                return;
            }
        }

        var token = ExtractToken(context);
        if (string.IsNullOrEmpty(token))
        {
            context.Response.StatusCode = StatusCodes.Status401Unauthorized;
            await context.Response.WriteAsJsonAsync(new { error = "Token bulunamadı. Lütfen giriş yapın." });
            return;
        }

        var principal = _jwtTokenService.ValidateToken(token);
        if (principal == null)
        {
            context.Response.StatusCode = StatusCodes.Status401Unauthorized;
            await context.Response.WriteAsJsonAsync(new { error = "Geçersiz token." });
            return;
        }

        context.User = principal;

        var requireRole = endpoint?.Metadata.GetMetadata<RequireRoleAttribute>();
        if (requireRole != null && requireRole.Roles.Length > 0)
        {
            var userRole = principal.FindFirst("systemRole")?.Value;
            if (userRole == null || !requireRole.Roles.Contains(userRole))
            {
                context.Response.StatusCode = StatusCodes.Status403Forbidden;
                await context.Response.WriteAsJsonAsync(new { error = "Bu işlem için yetkiniz bulunmamaktadır." });
                return;
            }
        }

        await _next(context);
    }

    private static string? ExtractToken(HttpContext context)
    {
        var authHeader = context.Request.Headers["Authorization"].FirstOrDefault();
        if (string.IsNullOrEmpty(authHeader) || !authHeader.StartsWith("Bearer ", StringComparison.OrdinalIgnoreCase))
        {
            return null;
        }

        return authHeader["Bearer ".Length..].Trim();
    }
}


