namespace Tinisoft.Infrastructure.Services;

public interface IAuditLogService
{
    Task LogAsync(string action, string entityType, Guid entityId, Guid? userId, string? changesJson = null, CancellationToken cancellationToken = default);
}

