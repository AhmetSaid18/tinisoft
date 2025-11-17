using Microsoft.AspNetCore.Http;
using Tinisoft.Domain.Entities;
using Tinisoft.Infrastructure.Persistence;
using Finbuckle.MultiTenant;

namespace Tinisoft.Infrastructure.Services;

public class AuditLogService : IAuditLogService
{
    private readonly ApplicationDbContext _dbContext;
    private readonly IHttpContextAccessor _httpContextAccessor;
    private readonly IMultiTenantContextAccessor<TenantInfo> _tenantAccessor;

    public AuditLogService(
        ApplicationDbContext dbContext,
        IHttpContextAccessor httpContextAccessor,
        IMultiTenantContextAccessor<TenantInfo> tenantAccessor)
    {
        _dbContext = dbContext;
        _httpContextAccessor = httpContextAccessor;
        _tenantAccessor = tenantAccessor;
    }

    public async Task LogAsync(string action, string entityType, Guid entityId, Guid? userId, string? changesJson = null, CancellationToken cancellationToken = default)
    {
        var tenantId = _tenantAccessor.MultiTenantContext?.TenantInfo?.Id;
        if (string.IsNullOrEmpty(tenantId)) return;

        var httpContext = _httpContextAccessor.HttpContext;
        var log = new AuditLog
        {
            TenantId = Guid.Parse(tenantId),
            UserId = userId,
            Action = action,
            EntityType = entityType,
            EntityId = entityId,
            ChangesJson = changesJson,
            IpAddress = httpContext?.Connection.RemoteIpAddress?.ToString(),
            UserAgent = httpContext?.Request.Headers["User-Agent"].ToString()
        };

        _dbContext.AuditLogs.Add(log);
        await _dbContext.SaveChangesAsync(cancellationToken);
    }
}

