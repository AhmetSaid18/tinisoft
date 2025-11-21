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

// CORS
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

