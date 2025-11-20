using Finbuckle.MultiTenant.EntityFrameworkCore;
using Finbuckle.MultiTenant.Stores;
using Microsoft.EntityFrameworkCore;
using Finbuckle.MultiTenant;
using Tinisoft.Infrastructure.MultiTenant;

namespace Tinisoft.Infrastructure.Persistence;

public class TenantStoreDbContext : EFCoreStoreDbContext<MultiTenant.TenantInfo>
{
    public TenantStoreDbContext(DbContextOptions<TenantStoreDbContext> options) : base(options)
    {
    }
}

