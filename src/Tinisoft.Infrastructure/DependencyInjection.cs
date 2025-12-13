using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Caching.StackExchangeRedis;
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
        else
        {
            // Redis yoksa null register et (RateLimitingMiddleware için)
            services.AddSingleton<IConnectionMultiplexer>(_ => null!);
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
        services.AddScoped<Tinisoft.Application.Common.Interfaces.IImageProcessingService, ImageProcessingService>();

        // PayTR (eski interface - backward compatibility için)
        services.AddHttpClient<Tinisoft.Application.Common.Interfaces.IPayTRService, PayTRService>();

        // Payment Services - HttpClient registration
        services.AddHttpClient<PayTRPaymentService>();
        services.AddHttpClient<KuveytTurkPaymentService>();

        // Marketplace Services - HttpClient registration
        services.AddHttpClient<Tinisoft.Application.Marketplace.Services.TrendyolMarketplaceService>();
        services.AddHttpClient<Tinisoft.Application.Marketplace.Services.HepsiburadaMarketplaceService>();
        services.AddHttpClient<Tinisoft.Application.Marketplace.Services.N11MarketplaceService>();

        // Shipping Services - HttpClient registration
        services.AddHttpClient<ArasShippingService>();
        services.AddHttpClient<MngShippingService>();
        services.AddHttpClient<YurticiShippingService>();

        // Hangfire Jobs
        services.AddScoped<Tinisoft.Infrastructure.Jobs.SyncMarketplaceProductsJob>();
        services.AddScoped<Tinisoft.Infrastructure.Jobs.SyncMarketplaceOrdersJob>();

        // Application services
        services.AddScoped<IAuditLogService, AuditLogService>();
        services.AddScoped<Tinisoft.Application.Common.Interfaces.ICacheService, CacheService>();
        services.AddScoped<Tinisoft.Application.Products.Services.IMeilisearchService, Tinisoft.Application.Products.Services.MeilisearchService>();
        services.AddScoped<Tinisoft.Application.Common.Interfaces.ICurrentCustomerService, CurrentCustomerService>();
        
        // Exchange Rate services
        services.AddHttpClient<Tinisoft.Application.ExchangeRates.Services.ITcmbExchangeService, TcmbExchangeService>();
        services.AddScoped<Tinisoft.Application.ExchangeRates.Services.IExchangeRateService, ExchangeRateService>();
        
        // Reseller Pricing Service
        services.AddScoped<Tinisoft.Application.Resellers.Services.IResellerPricingService, ResellerPricingService>();
        
        // Product Feed Service
        services.AddScoped<Tinisoft.Application.ProductFeeds.Services.IProductFeedService, ProductFeedService>();
        
        // Coupon Validation Service
        services.AddScoped<Tinisoft.Application.Discounts.Services.ICouponValidationService, CouponValidationService>();
        
        // Shipping Services
        services.AddScoped<ArasShippingService>();
        services.AddScoped<MngShippingService>();
        services.AddScoped<YurticiShippingService>();
        services.AddScoped<Tinisoft.Application.Shipping.Services.IShippingServiceFactory, ShippingServiceFactory>();
        
        // Payment Services
        services.AddScoped<PayTRPaymentService>();
        services.AddScoped<KuveytTurkPaymentService>();
        services.AddScoped<Tinisoft.Application.Payments.Services.IPaymentServiceFactory, PaymentServiceFactory>();
        
        // Email Service (SendGrid - production ready)
        services.AddScoped<Tinisoft.Application.Notifications.Services.IEmailService, SendGridEmailService>();
        
        // SMS Service (Netgsm - Türkiye için)
        services.AddHttpClient<Tinisoft.Application.Notifications.Services.ISmsService, NetgsmSmsService>();
        
        // Notification Service (Email + SMS orchestration)
        services.AddScoped<Tinisoft.Application.Notifications.Services.INotificationService, NotificationService>();
        
        // Marketplace Service Factory
        services.AddScoped<Tinisoft.Application.Marketplace.Services.IMarketplaceServiceFactory, Tinisoft.Application.Marketplace.Services.MarketplaceServiceFactory>();
        services.AddScoped<Tinisoft.Application.Marketplace.Services.TrendyolMarketplaceService>();
        services.AddScoped<Tinisoft.Application.Marketplace.Services.HepsiburadaMarketplaceService>();
        services.AddScoped<Tinisoft.Application.Marketplace.Services.N11MarketplaceService>();
        
        // Invoice Services
        services.AddScoped<Tinisoft.Application.Invoices.Services.IInvoiceNumberGenerator, InvoiceNumberGenerator>();
        services.AddScoped<Tinisoft.Application.Invoices.Services.IUBLXMLGenerator, UBLXMLGenerator>();
        services.AddHttpClient<Tinisoft.Application.Invoices.Services.IGIBService, GIBService>();
        services.AddScoped<Tinisoft.Application.Invoices.Services.IPDFGenerator, PDFGenerator>();
        
        // Jobs
        services.AddScoped<Jobs.SyncExchangeRatesJob>();
        services.AddScoped<Jobs.SyncInvoiceStatusFromGIBJob>();
        services.AddScoped<Jobs.DomainVerificationJob>();
        
        // Domain Management Services
        services.AddScoped<Tinisoft.Application.Common.Interfaces.IDnsVerificationService, DnsVerificationService>();
        services.AddScoped<Tinisoft.Application.Common.Interfaces.ITraefikDomainService, TraefikDomainService>();
        
        // Circuit Breaker - Database koruması için
        services.AddSingleton<Tinisoft.Shared.Contracts.ICircuitBreakerService, CircuitBreakerService>();

        // Authentication services
        services.AddScoped<Tinisoft.Application.Common.Interfaces.IJwtTokenService, JwtTokenService>();
        services.AddScoped<Tinisoft.Application.Common.Interfaces.IPasswordHasher, PasswordHasher>();
        
        // Tenant Store Service
        services.AddScoped<Tinisoft.Application.Common.Interfaces.ITenantStoreService, TenantStoreService>();

        // Event Bus - Hybrid (Kafka + RabbitMQ) veya sadece RabbitMQ
        var useKafka = !string.IsNullOrEmpty(configuration["Kafka:BootstrapServers"]);
        var useRabbitMQ = !string.IsNullOrEmpty(configuration["RabbitMQ:HostName"]);

        if (useKafka && useRabbitMQ)
        {
            // Hybrid: High-volume event'ler Kafka'ya, basit event'ler RabbitMQ'ya
            services.AddSingleton<Tinisoft.Infrastructure.EventBus.KafkaEventBus>();
            services.AddSingleton<Tinisoft.Infrastructure.EventBus.RabbitMQEventBus>();
            services.AddSingleton<Tinisoft.Shared.Contracts.IEventBus, Tinisoft.Infrastructure.EventBus.HybridEventBus>();
            
            // Kafka Consumer Service (Background Service)
            services.AddHostedService<Tinisoft.Infrastructure.EventBus.KafkaConsumerService>();
        }
        else if (useRabbitMQ)
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

