using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Tinisoft.Infrastructure.Persistence;
using Finbuckle.MultiTenant;
using Finbuckle.MultiTenant.Stores;
using Finbuckle.MultiTenant.AspNetCore;
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

        services.AddMultiTenant<MultiTenant.TenantInfo>()
            .WithHeaderStrategy("X-Tenant-Id")
            .WithHostStrategy() // Host header'dan tenant bulur
            .WithEFCoreStore<TenantStoreDbContext, MultiTenant.TenantInfo>();

        // Global DbContext (tenant'a bağlı olmayan entity'ler için - ExchangeRate, etc.)
        services.AddDbContext<GlobalDbContext>(options =>
            options.UseNpgsql(connectionString));

        // ApplicationDbContextFactory register et
        services.AddScoped<ApplicationDbContextFactory>(sp =>
        {
            var config = sp.GetRequiredService<IConfiguration>();
            var tenantAccessor = sp.GetService<IMultiTenantContextAccessor>();
            return new ApplicationDbContextFactory(config, tenantAccessor);
        });

        // ApplicationDbContext'i register et - Factory kullan
        services.AddScoped<ApplicationDbContext>(sp =>
        {
            var contextFactory = sp.GetRequiredService<ApplicationDbContextFactory>();
            return contextFactory.CreateDbContext();
        });

        // IApplicationDbContext interface'ini register et - Factory kullan
        services.AddScoped<Tinisoft.Application.Common.Interfaces.IApplicationDbContext>(sp =>
        {
            var contextFactory = sp.GetRequiredService<ApplicationDbContextFactory>();
            return contextFactory.CreateDbContext();
        });

        return services;
    }
}

