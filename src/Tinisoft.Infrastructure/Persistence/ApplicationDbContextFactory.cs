using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Configuration;
using Finbuckle.MultiTenant;
using Tinisoft.Infrastructure.MultiTenant;

namespace Tinisoft.Infrastructure.Persistence;

/// <summary>
/// ApplicationDbContext factory - Tenant context olmadan da çalışabilmeli (register işlemi için)
/// </summary>
public class ApplicationDbContextFactory
{
    private readonly IConfiguration _configuration;
    private readonly IMultiTenantContextAccessor? _tenantAccessor;

    public ApplicationDbContextFactory(
        IConfiguration configuration,
        IMultiTenantContextAccessor? tenantAccessor = null)
    {
        _configuration = configuration;
        _tenantAccessor = tenantAccessor;
    }

    public ApplicationDbContext CreateDbContext()
    {
        var connectionString = _configuration.GetConnectionString("DefaultConnection");
        var tenantInfo = _tenantAccessor?.MultiTenantContext?.TenantInfo as MultiTenant.TenantInfo;
        
        // Tenant yoksa (register işlemi gibi) geçici bir tenant context oluştur
        if (tenantInfo == null)
        {
            tenantInfo = new MultiTenant.TenantInfo
            {
                Id = Guid.Empty.ToString(),
                Identifier = "system",
                Name = "System",
                ConnectionString = string.Empty
            };
        }
        
        // Options oluştur
        var optionsBuilder = new DbContextOptionsBuilder<ApplicationDbContext>();
        optionsBuilder.UseNpgsql(connectionString, npgsqlOptions =>
        {
            npgsqlOptions.MigrationsAssembly("Tinisoft.Infrastructure");
            npgsqlOptions.MaxBatchSize(100);
            npgsqlOptions.CommandTimeout(30);
            npgsqlOptions.EnableRetryOnFailure(
                maxRetryCount: 3,
                maxRetryDelay: TimeSpan.FromSeconds(5),
                errorCodesToAdd: null);
        });
        optionsBuilder.UseQueryTrackingBehavior(QueryTrackingBehavior.NoTracking);
        
        // ApplicationDbContext'i tenantInfo ve options ile oluştur
        return new ApplicationDbContext(tenantInfo, optionsBuilder.Options);
    }
}

