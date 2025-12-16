using Tinisoft.Infrastructure;
using Tinisoft.Infrastructure.Persistence;
using Tinisoft.Infrastructure.Middleware;
using Tinisoft.Application;
using Microsoft.EntityFrameworkCore;
using Serilog;
using Tinisoft.Shipping.API.Middleware;

var builder = WebApplication.CreateBuilder(args);

// Serilog
Log.Logger = new LoggerConfiguration()
    .ReadFrom.Configuration(builder.Configuration)
    .Enrich.FromLogContext()
    .CreateLogger();

builder.Host.UseSerilog();

builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen(c =>
{
    c.SwaggerDoc("v1", new() { Title = "Shipping API", Version = "v1" });
});

// CORS - Sadece Gateway'den erişim (Docker network içinde)
builder.Services.AddCors(options =>
{
    options.AddDefaultPolicy(policy =>
    {
        policy.WithOrigins(
                "http://gateway:5000",
                "http://localhost:5000"
            )
            .AllowAnyMethod()
            .AllowAnyHeader()
            .AllowCredentials();
    });
});

// Application
builder.Services.AddApplication();

// Infrastructure - Shipping Database
builder.Services.AddInfrastructure(builder.Configuration);

// Health Checks
builder.Services.AddHealthChecks()
    .AddDbContextCheck<ApplicationDbContext>();

var app = builder.Build();

if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseMiddleware<ExceptionHandlingMiddleware>();
app.UseMiddleware<JwtAuthenticationMiddleware>();
app.UseMiddleware<RateLimitingMiddleware>();
app.UseHttpsRedirection();
app.UseCors();
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
        // Veritabanı bağlantısını kontrol et ve retry mekanizması
        var maxRetries = 5;
        var delay = TimeSpan.FromSeconds(5);
        for (int i = 0; i < maxRetries; i++)
        {
            try
            {
                if (await dbContext.Database.CanConnectAsync())
                {
                    Log.Information("Database connection successful");
                    break;
                }
            }
            catch (Exception)
            {
                if (i == maxRetries - 1)
                {
                    Log.Error("Failed to connect to database after {MaxRetries} attempts", maxRetries);
                    throw;
                }
                Log.Warning("Database connection failed, retrying in {Delay} seconds... (Attempt {Attempt}/{MaxRetries})", 
                    delay.TotalSeconds, i + 1, maxRetries);
                await Task.Delay(delay);
            }
        }

        // Migration yoksa EnsureCreated kullan (migration dosyaları olmadığı için)
        // Migration history tablosunu manuel oluştur
        try
        {
            var connectionString = builder.Configuration.GetConnectionString("DefaultConnection");
            var searchPath = connectionString?.Split(';')
                .FirstOrDefault(p => p.Trim().StartsWith("SearchPath", StringComparison.OrdinalIgnoreCase))
                ?.Split('=')[1]?.Trim();
            
            var schema = !string.IsNullOrEmpty(searchPath) ? searchPath : "public";
            
            // Migration history tablosunu manuel oluştur
            var createTableSql = $@"
                CREATE TABLE IF NOT EXISTS {(schema != "public" ? $@"""{schema}""." : "")}__EFMigrationsHistory (
                    ""MigrationId"" VARCHAR(150) NOT NULL PRIMARY KEY,
                    ""ProductVersion"" VARCHAR(32) NOT NULL
                );";
            
            await dbContext.Database.ExecuteSqlRawAsync(createTableSql);
            
            // EnsureCreated kullanarak tabloları oluştur (migration olmadığı için)
            var created = await dbContext.Database.EnsureCreatedAsync();
            if (created)
            {
                // Initial migration kaydını ekle
                await dbContext.Database.ExecuteSqlRawAsync(
                    $@"INSERT INTO {(schema != "public" ? $@"""{schema}""." : "")}__EFMigrationsHistory (""MigrationId"", ""ProductVersion"") 
                       VALUES ('InitialCreate', '8.0.4') 
                       ON CONFLICT (""MigrationId"") DO NOTHING");
                Log.Information("Database created successfully using EnsureCreated in schema: {Schema}", schema);
            }
            else
            {
                Log.Information("Database already exists in schema: {Schema}", schema);
            }
        }
        catch (Exception ex)
        {
            Log.Error(ex, "Error creating database");
            // Development'ta throw etme, sadece log'la
            if (!app.Environment.IsDevelopment())
            {
                throw;
            }
        }
    }
    catch (Exception ex)
    {
        Log.Error(ex, "Error applying database migrations");
        // Development'ta throw etme, sadece log'la
        if (!app.Environment.IsDevelopment())
        {
            throw;
        }
    }
}

app.Urls.Add("http://0.0.0.0:5007");
app.Run();

