using Ocelot.DependencyInjection;
using Ocelot.Middleware;

var builder = WebApplication.CreateBuilder(args);

builder.Configuration
    .SetBasePath(builder.Environment.ContentRootPath)
    .AddJsonFile("ocelot.json", optional: false, reloadOnChange: true)
    .AddEnvironmentVariables();

builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

// Ocelot
builder.Services.AddOcelot(builder.Configuration);

// CORS - Frontend origin'leri: tinisoft.com.tr ve localhost:3000
builder.Services.AddCors(options =>
{
    // Frontend için CORS (process, verify endpoint'leri)
    options.AddDefaultPolicy(policy =>
    {
        policy.WithOrigins(
                "http://localhost:3000",
                "https://tinisoft.com.tr",
                "https://www.tinisoft.com.tr"
            )
            .AllowAnyMethod()
            .AllowAnyHeader()
            .AllowCredentials(); // JWT token için gerekli
    });

    // Payment callback'ler için (ödeme sağlayıcılarından gelecek - CORS gerekmez ama güvenlik için)
    options.AddPolicy("PaymentCallback", policy =>
    {
        policy.AllowAnyOrigin() // Ödeme sağlayıcıları farklı origin'lerden gelebilir
            .AllowAnyMethod()
            .AllowAnyHeader();
    });
});

var app = builder.Build();

if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseCors();
app.UseOcelot().Wait();
app.UseAuthorization();
app.MapControllers();

app.Urls.Add("http://0.0.0.0:5000");
app.Run();

