using Tinisoft.Infrastructure;
using Tinisoft.Infrastructure.Persistence;
using Tinisoft.Infrastructure.Jobs;
using Tinisoft.Application;
using Microsoft.EntityFrameworkCore;
using Serilog;
using Tinisoft.API.Middleware;
using Hangfire;

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
builder.Services.AddSwaggerGen();

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
        policy.AllowAnyOrigin()
              .AllowAnyMethod()
              .AllowAnyHeader();
    });
});

// Application servisleri
builder.Services.AddApplication();

// Infrastructure servisleri
builder.Services.AddInfrastructure(builder.Configuration);

// Health Checks
builder.Services.AddHealthChecks()
    .AddDbContextCheck<ApplicationDbContext>();

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

// Database migration - Development veya RUN_MIGRATIONS=true ise çalıştır
var runMigrations = app.Environment.IsDevelopment() || 
                     builder.Configuration.GetValue<bool>("RunMigrations", false);
if (runMigrations)
{
    using var scope = app.Services.CreateScope();
    var dbContext = scope.ServiceProvider.GetRequiredService<ApplicationDbContext>();
    try
    {
        await dbContext.Database.MigrateAsync();
        Log.Information("Database migrations applied successfully");
    }
    catch (Exception ex)
    {
        Log.Error(ex, "Error applying database migrations");
        throw;
    }
}

// Schedule Hangfire Jobs
using (var scope = app.Services.CreateScope())
{
    var recurringJobManager = scope.ServiceProvider.GetRequiredService<IRecurringJobManager>();
    
    // Exchange Rate Sync Job - Her saat başı çalışsın
    recurringJobManager.AddOrUpdate(
        "sync-exchange-rates",
        () => scope.ServiceProvider.GetRequiredService<SyncExchangeRatesJob>().ExecuteAsync(CancellationToken.None),
        Cron.Hourly,
        new RecurringJobOptions
        {
            TimeZone = TimeZoneInfo.FindSystemTimeZoneById("Turkey Standard Time")
        });

    // Invoice Status Sync Job - Her 30 dakikada bir çalışsın
    recurringJobManager.AddOrUpdate(
        "sync-invoice-status-from-gib",
        () => scope.ServiceProvider.GetRequiredService<SyncInvoiceStatusFromGIBJob>().ExecuteAsync(CancellationToken.None),
        "*/30 * * * *", // Her 30 dakikada bir
        new RecurringJobOptions
        {
            TimeZone = TimeZoneInfo.FindSystemTimeZoneById("Turkey Standard Time")
        });
}

app.Urls.Add("http://0.0.0.0:5010");
app.Run();

