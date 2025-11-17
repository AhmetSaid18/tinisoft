using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Tinisoft.Infrastructure.Persistence;
using Finbuckle.MultiTenant;
using Finbuckle.MultiTenant.Stores;
using Tinisoft.Infrastructure.MultiTenant;

namespace Tinisoft.Infrastructure.Persistence;

public static class DependencyInjection
{
    public static IServiceCollection AddPersistence(this IServiceCollection services, IConfiguration configuration)
    {
        var connectionString = configuration.GetConnectionString("DefaultConnection");

        // Multi-tenant store (EF Core)
        services.AddDbContext<TenantStoreDbContext>(options =>
            options.UseNpgsql(connectionString));

        services.AddMultiTenant<TenantInfo>()
            .WithHeaderStrategy("X-Tenant-Id")
            .WithHostStrategy() // Host header'dan tenant bulur
            .WithEFCoreStore<TenantStoreDbContext, TenantInfo>();

        // Application DbContext
        services.AddDbContext<ApplicationDbContext>(options =>
        {
            options.UseNpgsql(connectionString);
            options.UseQueryTrackingBehavior(QueryTrackingBehavior.NoTracking);
        });

        services.AddScoped<ApplicationDbContext>();

        return services;
    }
}

