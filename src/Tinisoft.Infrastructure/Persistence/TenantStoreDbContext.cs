using Finbuckle.MultiTenant.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore;
using Finbuckle.MultiTenant;
using Tinisoft.Infrastructure.MultiTenant;

namespace Tinisoft.Infrastructure.Persistence;

public class TenantStoreDbContext : EFCoreStoreDbContext<TenantInfo>
{
    public TenantStoreDbContext(DbContextOptions<TenantStoreDbContext> options) : base(options)
    {
    }

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.ConfigureMultiTenant();
        base.OnModelCreating(modelBuilder);
    }
}

