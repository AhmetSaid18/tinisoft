using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
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

        // Global DbContext (tenant'a bağlı olmayan entity'ler için - ExchangeRate, etc.)
        services.AddDbContext<GlobalDbContext>(options =>
            options.UseNpgsql(connectionString));

        // Application DbContext
        services.AddDbContext<ApplicationDbContext>(options =>
        {
            options.UseNpgsql(connectionString, npgsqlOptions =>
            {
                // PostgreSQL UUID extension'ını kullan
                npgsqlOptions.MigrationsAssembly("Tinisoft.Infrastructure");
                
                // Connection Pooling - CRITICAL: Cold start için yeterli pool size
                // 1000 tenant aynı anda istek atarsa yeterli connection olmalı
                // PostgreSQL default: min=0, max=100
                // Connection string'de: MinPoolSize=50;MaxPoolSize=200;Connection Lifetime=0;
                // (appsettings.json'da connection string'e eklenecek)
                
                npgsqlOptions.MaxBatchSize(100); // Batch size
                npgsqlOptions.CommandTimeout(30); // 30 saniye timeout
                
                // Enable retry on failure (transient errors için)
                npgsqlOptions.EnableRetryOnFailure(
                    maxRetryCount: 3,
                    maxRetryDelay: TimeSpan.FromSeconds(5),
                    errorCodesToAdd: null);
            });
            
            // Query Tracking - Read-only query'ler için NoTracking (performans)
            options.UseQueryTrackingBehavior(QueryTrackingBehavior.NoTracking);
            
            // Query Splitting - N+1 problem'ini önlemek için
            options.UseQuerySplittingBehavior(QuerySplittingBehavior.SplitQuery);
            
            // Enable sensitive data logging sadece development'ta
            // Not: Environment kontrolü için IWebHostEnvironment kullanılabilir
        });

        services.AddScoped<ApplicationDbContext>();

        return services;
    }
}

