using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Tinisoft.Domain.Entities;

namespace Tinisoft.Infrastructure.Persistence;

public class DatabaseSeeder
{
    private readonly ApplicationDbContext _dbContext;
    private readonly ILogger<DatabaseSeeder> _logger;

    public DatabaseSeeder(ApplicationDbContext dbContext, ILogger<DatabaseSeeder> logger)
    {
        _dbContext = dbContext;
        _logger = logger;
    }

    public async Task SeedAsync()
    {
        // Templates artık frontend'den sync edilecek (SyncTemplates API)
        // Sadece Plans seed ediliyor
        await SeedPlansAsync();
    }

    private async Task SeedPlansAsync()
    {
        // Zaten plan varsa ekleme
        if (await _dbContext.Plans.AnyAsync())
        {
            _logger.LogInformation("Plans already seeded, skipping...");
            return;
        }

        var plans = new List<Plan>
        {
            new Plan
            {
                Id = Guid.NewGuid(),
                Name = "Free",
                Description = "Başlangıç için ücretsiz plan - Tüm özellikler sınırlı",
                MonthlyPrice = 0,
                YearlyPrice = 0,
                MaxProducts = 10,
                MaxOrdersPerMonth = 50,
                MaxStorageGB = 1,
                CustomDomainEnabled = false,
                AdvancedAnalytics = false,
                IsActive = true,
                CreatedAt = DateTime.UtcNow,
                UpdatedAt = DateTime.UtcNow
            },
            new Plan
            {
                Id = Guid.NewGuid(),
                Name = "Starter",
                Description = "Küçük işletmeler için ideal başlangıç planı",
                MonthlyPrice = 299,
                YearlyPrice = 2990, // ~17% indirim
                MaxProducts = 100,
                MaxOrdersPerMonth = 500,
                MaxStorageGB = 5,
                CustomDomainEnabled = false,
                AdvancedAnalytics = false,
                IsActive = true,
                CreatedAt = DateTime.UtcNow,
                UpdatedAt = DateTime.UtcNow
            },
            new Plan
            {
                Id = Guid.NewGuid(),
                Name = "Professional",
                Description = "Büyüyen işletmeler için gelişmiş özellikler",
                MonthlyPrice = 599,
                YearlyPrice = 5990, // ~17% indirim
                MaxProducts = 1000,
                MaxOrdersPerMonth = 2000,
                MaxStorageGB = 25,
                CustomDomainEnabled = true,
                AdvancedAnalytics = true,
                IsActive = true,
                CreatedAt = DateTime.UtcNow,
                UpdatedAt = DateTime.UtcNow
            },
            new Plan
            {
                Id = Guid.NewGuid(),
                Name = "Enterprise",
                Description = "Kurumsal müşteriler için sınırsız erişim ve özel destek",
                MonthlyPrice = 1499,
                YearlyPrice = 14990, // ~17% indirim
                MaxProducts = -1, // Unlimited
                MaxOrdersPerMonth = -1, // Unlimited
                MaxStorageGB = 100,
                CustomDomainEnabled = true,
                AdvancedAnalytics = true,
                IsActive = true,
                CreatedAt = DateTime.UtcNow,
                UpdatedAt = DateTime.UtcNow
            }
        };

        await _dbContext.Plans.AddRangeAsync(plans);
        await _dbContext.SaveChangesAsync();

        _logger.LogInformation("Seeded {Count} plans", plans.Count);
    }
}

public static class DatabaseSeederExtensions
{
    public static async Task SeedDatabaseAsync(this IServiceProvider serviceProvider)
    {
        using var scope = serviceProvider.CreateScope();
        var dbContext = scope.ServiceProvider.GetRequiredService<ApplicationDbContext>();
        var logger = scope.ServiceProvider.GetRequiredService<ILogger<DatabaseSeeder>>();
        
        var seeder = new DatabaseSeeder(dbContext, logger);
        await seeder.SeedAsync();
    }
}
