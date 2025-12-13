using Microsoft.EntityFrameworkCore;
using Tinisoft.Application.Common.Interfaces;
using Tinisoft.Infrastructure.MultiTenant;
using Tinisoft.Infrastructure.Persistence;

namespace Tinisoft.Infrastructure.Services;

public class TenantStoreService : ITenantStoreService
{
    private readonly TenantStoreDbContext _dbContext;

    public TenantStoreService(TenantStoreDbContext dbContext)
    {
        _dbContext = dbContext;
    }

    public async Task AddTenantAsync(string tenantId, string identifier, string name, CancellationToken cancellationToken = default)
    {
        var tenantInfo = new MultiTenant.TenantInfo
        {
            Id = tenantId,
            Identifier = identifier,
            Name = name,
            ConnectionString = string.Empty // Shared database kullanıyoruz, connection string gerekmez
        };
        
        _dbContext.TenantInfo.Add(tenantInfo);
        await _dbContext.SaveChangesAsync(cancellationToken);
    }
}

