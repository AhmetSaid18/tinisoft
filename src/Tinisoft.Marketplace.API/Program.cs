using Tinisoft.Infrastructure;
using Tinisoft.Infrastructure.Persistence;
using Tinisoft.Infrastructure.Middleware;
using Tinisoft.Application;
using Microsoft.EntityFrameworkCore;
using Serilog;
using Tinisoft.Marketplace.API.Middleware;
using Tinisoft.Application.Marketplace.Services;

var builder = WebApplication.CreateBuilder(args);

Log.Logger = new LoggerConfiguration()
    .ReadFrom.Configuration(builder.Configuration)
    .Enrich.FromLogContext()
    .CreateLogger();

builder.Host.UseSerilog();

builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen(c =>
{
    c.SwaggerDoc("v1", new() { Title = "Marketplace API", Version = "v1" });
});

builder.Services.AddCors(options =>
{
    options.AddDefaultPolicy(policy =>
    {
        policy.AllowAnyOrigin()
              .AllowAnyMethod()
              .AllowAnyHeader();
    });
});

builder.Services.AddApplication();
builder.Services.AddInfrastructure(builder.Configuration);

// Marketplace Services
builder.Services.AddScoped<TrendyolMarketplaceService>();
builder.Services.AddScoped<HepsiburadaMarketplaceService>();
builder.Services.AddScoped<N11MarketplaceService>();
builder.Services.AddScoped<IMarketplaceServiceFactory, MarketplaceServiceFactory>();

builder.Services.AddHealthChecks()
    .AddDbContextCheck<ApplicationDbContext>();

var app = builder.Build();

if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseMiddleware<ExceptionHandlingMiddleware>();
app.UseMiddleware<RateLimitingMiddleware>();
app.UseHttpsRedirection();
app.UseCors();
app.UseAuthorization();
app.MapControllers();
app.MapHealthChecks("/health");

if (app.Environment.IsDevelopment())
{
    using var scope = app.Services.CreateScope();
    var dbContext = scope.ServiceProvider.GetRequiredService<ApplicationDbContext>();
    await dbContext.Database.MigrateAsync();
}

app.Urls.Add("http://0.0.0.0:5005");
app.Run();

