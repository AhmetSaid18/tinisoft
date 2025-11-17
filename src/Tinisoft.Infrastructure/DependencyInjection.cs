using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Tinisoft.Infrastructure.Persistence;
using Tinisoft.Infrastructure.Services;
using StackExchange.Redis;
using Hangfire;
using Hangfire.PostgreSql;
using Meilisearch;
using Microsoft.AspNetCore.Http;

namespace Tinisoft.Infrastructure;

public static class DependencyInjection
{
    public static IServiceCollection AddInfrastructure(this IServiceCollection services, IConfiguration configuration)
    {
        // Persistence
        services.AddPersistence(configuration);

        // HTTP Context
        services.AddHttpContextAccessor();

        // Redis
        var redisConnectionString = configuration.GetSection("Redis:ConnectionString").Value;
        if (!string.IsNullOrEmpty(redisConnectionString))
        {
            var redis = ConnectionMultiplexer.Connect(redisConnectionString);
            services.AddSingleton<IConnectionMultiplexer>(redis);
            services.AddStackExchangeRedisCache(options =>
            {
                options.Configuration = redisConnectionString;
            });
        }

        // Hangfire
        var connectionString = configuration.GetConnectionString("DefaultConnection");
        services.AddHangfire(config => config
            .SetDataCompatibilityLevel(CompatibilityLevel.Version_180)
            .UseSimpleAssemblyNameTypeSerializer()
            .UseRecommendedSerializerSettings()
            .UsePostgreSqlStorage(connectionString));

        services.AddHangfireServer();

        // Meilisearch
        var meilisearchHost = configuration.GetSection("Meilisearch:Host").Value;
        var meilisearchApiKey = configuration.GetSection("Meilisearch:ApiKey").Value;
        if (!string.IsNullOrEmpty(meilisearchHost))
        {
            services.AddSingleton<MeilisearchClient>(sp =>
                new MeilisearchClient(meilisearchHost, meilisearchApiKey));
        }

        // Storage (R2/S3)
        services.AddScoped<IStorageService, R2StorageService>();

        // Image Processing
        services.AddScoped<IImageProcessingService, ImageProcessingService>();

        // PayTR
        services.AddHttpClient<IPayTRService, PayTRService>();

        // Application services
        services.AddScoped<IAuditLogService, AuditLogService>();

        // Event Bus - RabbitMQ veya InMemory
        var useRabbitMQ = !string.IsNullOrEmpty(configuration["RabbitMQ:HostName"]);
        if (useRabbitMQ)
        {
            services.AddSingleton<Tinisoft.Shared.Contracts.IEventBus, Tinisoft.Infrastructure.EventBus.RabbitMQEventBus>();
        }
        else
        {
            services.AddSingleton<Tinisoft.Shared.Contracts.IEventBus, Tinisoft.Shared.Contracts.InMemoryEventBus>();
        }

        return services;
    }
}

