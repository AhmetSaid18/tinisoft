using System.IdentityModel.Tokens.Jwt;
using System.Security.Claims;
using Tinisoft.API.Attributes;
using Tinisoft.Infrastructure.Services;

namespace Tinisoft.API.Middleware;

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
        // Public endpoint kontrolü
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

        // Token kontrolü
        var token = ExtractToken(context);
        if (string.IsNullOrEmpty(token))
        {
            context.Response.StatusCode = 401;
            await context.Response.WriteAsJsonAsync(new { error = "Token bulunamadı. Lütfen giriş yapın." });
            return;
        }

        // Token doğrulama
        var principal = _jwtTokenService.ValidateToken(token);
        if (principal == null)
        {
            context.Response.StatusCode = 401;
            await context.Response.WriteAsJsonAsync(new { error = "Geçersiz token." });
            return;
        }

        // Claims'i context'e ekle
        context.User = principal;

        // Role kontrolü
        var requireRole = endpoint?.Metadata.GetMetadata<RequireRoleAttribute>();
        if (requireRole != null && requireRole.Roles.Length > 0)
        {
            var userRole = principal.FindFirst("systemRole")?.Value;
            if (userRole == null || !requireRole.Roles.Contains(userRole))
            {
                context.Response.StatusCode = 403;
                await context.Response.WriteAsJsonAsync(new { error = "Bu işlem için yetkiniz bulunmamaktadır." });
                return;
            }
        }

        await _next(context);
    }

    private string? ExtractToken(HttpContext context)
    {
        // Authorization header'dan token al
        var authHeader = context.Request.Headers["Authorization"].FirstOrDefault();
        if (string.IsNullOrEmpty(authHeader) || !authHeader.StartsWith("Bearer ", StringComparison.OrdinalIgnoreCase))
        {
            return null;
        }

        return authHeader.Substring("Bearer ".Length).Trim();
    }
}

