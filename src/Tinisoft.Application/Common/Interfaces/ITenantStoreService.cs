namespace Tinisoft.Application.Common.Interfaces;

/// <summary>
/// Tenant store service - Finbuckle.MultiTenant için tenant bilgilerini yönetir
/// </summary>
public interface ITenantStoreService
{
    Task AddTenantAsync(string tenantId, string identifier, string name, CancellationToken cancellationToken = default);
}

