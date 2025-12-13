using Tinisoft.Infrastructure;
using Tinisoft.Infrastructure.Persistence;
using Tinisoft.Infrastructure.Jobs;
using Tinisoft.Application;
using Microsoft.EntityFrameworkCore;
using Serilog;
using Tinisoft.API.Middleware;
using Hangfire;
using Tinisoft.Domain.Entities;
using StackExchange.Redis;
using Hangfire.Dashboard;

var builder = WebApplication.CreateBuilder(args);

// Serilog yapılandırması
Log.Logger = new LoggerConfiguration()
    .ReadFrom.Configuration(builder.Configuration)
    .Enrich.FromLogContext()
    .CreateLogger();

builder.Host.UseSerilog();

// Add services to the container.
builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen(options =>
{
    options.SwaggerDoc("v1", new Microsoft.OpenApi.Models.OpenApiInfo
    {
        Title = "Tinisoft E-Commerce API",
        Version = "v1",
        Description = "Multi-tenant E-Commerce Platform API",
        Contact = new Microsoft.OpenApi.Models.OpenApiContact
        {
            Name = "Tinisoft Support",
            Email = "support@tinisoft.com"
        }
    });
    
    // JWT Authentication için Swagger UI
    options.AddSecurityDefinition("Bearer", new Microsoft.OpenApi.Models.OpenApiSecurityScheme
    {
        Name = "Authorization",
        Type = Microsoft.OpenApi.Models.SecuritySchemeType.Http,
        Scheme = "Bearer",
        BearerFormat = "JWT",
        In = Microsoft.OpenApi.Models.ParameterLocation.Header,
        Description = "JWT Authorization header. Example: \"Bearer {token}\""
    });
    
    options.AddSecurityRequirement(new Microsoft.OpenApi.Models.OpenApiSecurityRequirement
    {
        {
            new Microsoft.OpenApi.Models.OpenApiSecurityScheme
            {
                Reference = new Microsoft.OpenApi.Models.OpenApiReference
                {
                    Type = Microsoft.OpenApi.Models.ReferenceType.SecurityScheme,
                    Id = "Bearer"
                }
            },
            Array.Empty<string>()
        }
    });
});

// Response Compression (Performans için)
builder.Services.AddResponseCompression(options =>
{
    options.EnableForHttps = true;
    options.Providers.Add<Microsoft.AspNetCore.ResponseCompression.BrotliCompressionProvider>();
    options.Providers.Add<Microsoft.AspNetCore.ResponseCompression.GzipCompressionProvider>();
});

// CORS ayarları - dışarıdan istekler için
builder.Services.AddCors(options =>
{
    options.AddDefaultPolicy(policy =>
    {
        policy.WithOrigins(
                "http://localhost:3000",
                "http://localhost:3001",
                "http://localhost:3002",
                "http://localhost:3003",
                "https://tinisoft.com.tr",
                "https://www.tinisoft.com.tr",
                "https://app.tinisoft.com.tr",
                "https://admin.tinisoft.com.tr"
            )
            .AllowAnyMethod()
            .AllowAnyHeader()
            .AllowCredentials(); // JWT token için gerekli
    });
});

// Application servisleri
builder.Services.AddApplication();

// Infrastructure servisleri
builder.Services.AddInfrastructure(builder.Configuration);

// Health Checks - Production ready
var redisConnectionString = builder.Configuration.GetSection("Redis:ConnectionString").Value;
var rabbitMqHost = builder.Configuration.GetSection("RabbitMQ:HostName").Value;

var healthChecksBuilder = builder.Services.AddHealthChecks()
    .AddDbContextCheck<ApplicationDbContext>("database")
    .AddHangfire(options => options.MinimumAvailableServers = 1, name: "hangfire", tags: new[] { "jobs" });

// Redis health check (eğer connection string varsa)
if (!string.IsNullOrEmpty(redisConnectionString))
{
    healthChecksBuilder.AddRedis(redisConnectionString, name: "redis", tags: new[] { "cache" });
}

// RabbitMQ health check (eğer host varsa)
if (!string.IsNullOrEmpty(rabbitMqHost))
{
    var rabbitMqUser = builder.Configuration["RabbitMQ:UserName"] ?? "guest";
    var rabbitMqPassword = builder.Configuration["RabbitMQ:Password"] ?? "guest";
    var rabbitMqPort = builder.Configuration["RabbitMQ:Port"] ?? "5672";
    var rabbitMqUri = $"amqp://{rabbitMqUser}:{rabbitMqPassword}@{rabbitMqHost}:{rabbitMqPort}";
    healthChecksBuilder.AddRabbitMQ(
        rabbitMqUri,
        name: "rabbitmq", 
        tags: new[] { "messaging" });
}

var app = builder.Build();

// Configure the HTTP request pipeline.
if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseMiddleware<ExceptionHandlingMiddleware>();

// Response Compression
app.UseResponseCompression();

app.UseHttpsRedirection();

app.UseCors();

// JWT Authentication Middleware (kendi middleware'imiz)
app.UseMiddleware<JwtAuthenticationMiddleware>();

app.UseAuthentication();
app.UseAuthorization();

app.MapControllers();
app.MapHealthChecks("/health");
app.MapHealthChecks("/health/ready", new Microsoft.AspNetCore.Diagnostics.HealthChecks.HealthCheckOptions
{
    Predicate = check => check.Tags.Contains("ready")
});
app.MapHealthChecks("/health/live", new Microsoft.AspNetCore.Diagnostics.HealthChecks.HealthCheckOptions
{
    Predicate = _ => false // Sadece app'in ayakta olduğunu kontrol et
});

// Hangfire Dashboard (sadece development veya admin)
if (app.Environment.IsDevelopment())
{
    app.MapHangfireDashboard("/hangfire");
}
else
{
    app.MapHangfireDashboard("/hangfire", new DashboardOptions
    {
        Authorization = new[] { new Tinisoft.API.Middleware.HangfireDashboardAuthFilter() }
    });
}

// Database migration - Development veya RUN_MIGRATIONS=true ise çalıştır
var runMigrations = app.Environment.IsDevelopment() || 
                     builder.Configuration.GetValue<bool>("RunMigrations", false);
if (runMigrations)
{
    using var scope = app.Services.CreateScope();
    var dbContext = scope.ServiceProvider.GetRequiredService<ApplicationDbContext>();
    try
    {
        // Önce migration'ı çalıştır
        await dbContext.Database.MigrateAsync();
        Log.Information("Database migrations applied successfully");
    }
    catch (Exception ex)
    {
        Log.Error(ex, "Error applying database migrations");
        // Migration hatası olsa bile container'ı durdurma, sadece log'la
        // throw; // Production'da throw edebiliriz ama development'ta devam etsin
    }
}

// Seed database with initial data (Templates, Plans, etc.) - Migration'dan SONRA çalışmalı
if (app.Environment.IsDevelopment() || Environment.GetEnvironmentVariable("SEED_DATABASE") == "true")
{
    try
    {
        await app.Services.SeedDatabaseAsync();
    }
    catch (Exception seedEx)
    {
        Log.Warning(seedEx, "Error seeding database (migrations may not have completed)");
        // Seed hatası kritik değil, devam et
    }
}

// Schedule Hangfire Jobs
using (var scope = app.Services.CreateScope())
{
    var recurringJobManager = scope.ServiceProvider.GetRequiredService<IRecurringJobManager>();
    var turkeyTimeZone = TimeZoneInfo.FindSystemTimeZoneById("Turkey Standard Time");
    
    // Exchange Rate Sync Job - Her saat başı çalışsın
    recurringJobManager.AddOrUpdate(
        "sync-exchange-rates",
        () => scope.ServiceProvider.GetRequiredService<SyncExchangeRatesJob>().ExecuteAsync(CancellationToken.None),
        Cron.Hourly,
        new RecurringJobOptions { TimeZone = turkeyTimeZone });

    // Invoice Status Sync Job - Her 30 dakikada bir çalışsın
    recurringJobManager.AddOrUpdate(
        "sync-invoice-status-from-gib",
        () => scope.ServiceProvider.GetRequiredService<SyncInvoiceStatusFromGIBJob>().ExecuteAsync(CancellationToken.None),
        "*/30 * * * *",
        new RecurringJobOptions { TimeZone = turkeyTimeZone });

    // Marketplace Products Sync Job - Her 2 saatte bir
    recurringJobManager.AddOrUpdate(
        "sync-marketplace-products",
        () => scope.ServiceProvider.GetRequiredService<SyncMarketplaceProductsJob>().ExecuteAsync(CancellationToken.None),
        "0 */2 * * *",
        new RecurringJobOptions { TimeZone = turkeyTimeZone });

    // Marketplace Orders Sync Job - Her 15 dakikada bir
    recurringJobManager.AddOrUpdate(
        "sync-marketplace-orders",
        () => scope.ServiceProvider.GetRequiredService<SyncMarketplaceOrdersJob>().ExecuteAsync(CancellationToken.None),
        "*/15 * * * *",
        new RecurringJobOptions { TimeZone = turkeyTimeZone });

    // Domain Verification Job - Her 5 dakikada bir
    recurringJobManager.AddOrUpdate(
        "verify-pending-domains",
        () => scope.ServiceProvider.GetRequiredService<Tinisoft.Infrastructure.Jobs.DomainVerificationJob>().ExecuteAsync(CancellationToken.None),
        "*/5 * * * *",
        new RecurringJobOptions { TimeZone = turkeyTimeZone });
}

app.Urls.Add("http://0.0.0.0:5010");

app.Run();

