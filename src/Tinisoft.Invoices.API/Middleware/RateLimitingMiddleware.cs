using StackExchange.Redis;
using Finbuckle.MultiTenant;

namespace Tinisoft.Invoices.API.Middleware;

public class RateLimitingMiddleware
{
    private readonly RequestDelegate _next;
    private readonly IConnectionMultiplexer _redis;
    private readonly ILogger<RateLimitingMiddleware> _logger;
    private readonly IMultiTenantContextAccessor _tenantAccessor;

    private const int MaxRequestsPerMinute = 100;
    private const int MaxRequestsPerHour = 1000;
    private const int MaxRequestsPerDay = 10000;

    public RateLimitingMiddleware(
        RequestDelegate next,
        IConnectionMultiplexer redis,
        ILogger<RateLimitingMiddleware> logger,
        IMultiTenantContextAccessor tenantAccessor)
    {
        _next = next;
        _redis = redis;
        _logger = logger;
        _tenantAccessor = tenantAccessor;
    }

    public async Task InvokeAsync(HttpContext context)
    {
        var db = _redis.GetDatabase();
        var ipAddress = context.Connection.RemoteIpAddress?.ToString() ?? "unknown";
        var tenantId = _tenantAccessor.MultiTenantContext?.TenantInfo?.Id ?? "unknown";
        
        // Rate limit key: tenant + IP
        var key = $"ratelimit:{tenantId}:{ipAddress}";
        
        // Check per minute
        var minuteKey = $"{key}:minute:{DateTime.UtcNow:yyyyMMddHHmm}";
        var minuteCount = await db.StringIncrementAsync(minuteKey);
        await db.KeyExpireAsync(minuteKey, TimeSpan.FromMinutes(1));
        
        if (minuteCount > MaxRequestsPerMinute)
        {
            _logger.LogWarning("Rate limit exceeded for {TenantId} - {IpAddress} (minute: {Count})", 
                tenantId, ipAddress, minuteCount);
            await ReturnRateLimitError(context, "Too many requests per minute");
            return;
        }
        
        // Check per hour
        var hourKey = $"{key}:hour:{DateTime.UtcNow:yyyyMMddHH}";
        var hourCount = await db.StringIncrementAsync(hourKey);
        await db.KeyExpireAsync(hourKey, TimeSpan.FromHours(1));
        
        if (hourCount > MaxRequestsPerHour)
        {
            _logger.LogWarning("Rate limit exceeded for {TenantId} - {IpAddress} (hour: {Count})", 
                tenantId, ipAddress, hourCount);
            await ReturnRateLimitError(context, "Too many requests per hour");
            return;
        }
        
        // Check per day
        var dayKey = $"{key}:day:{DateTime.UtcNow:yyyyMMdd}";
        var dayCount = await db.StringIncrementAsync(dayKey);
        await db.KeyExpireAsync(dayKey, TimeSpan.FromDays(1));
        
        if (dayCount > MaxRequestsPerDay)
        {
            _logger.LogWarning("Rate limit exceeded for {TenantId} - {IpAddress} (day: {Count})", 
                tenantId, ipAddress, dayCount);
            await ReturnRateLimitError(context, "Too many requests per day");
            return;
        }

        await _next(context);
    }

    private static Task ReturnRateLimitError(HttpContext context, string message)
    {
        context.Response.StatusCode = 429;
        context.Response.ContentType = "application/json";
        return context.Response.WriteAsync($"{{\"error\": \"{message}\"}}");
    }
}

