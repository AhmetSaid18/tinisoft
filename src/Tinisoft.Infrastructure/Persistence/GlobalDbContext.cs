using Microsoft.EntityFrameworkCore;
using Tinisoft.Domain.Entities;

namespace Tinisoft.Infrastructure.Persistence;

/// <summary>
/// Global entities için DbContext (tenant'a bağlı olmayan)
/// ExchangeRate gibi global entity'ler için kullanılır
/// </summary>
public class GlobalDbContext : DbContext
{
    public GlobalDbContext(DbContextOptions<GlobalDbContext> options) : base(options)
    {
    }

    public DbSet<ExchangeRate> ExchangeRates => Set<ExchangeRate>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);

        // Tüm Guid property'ler için PostgreSQL UUID type'ını kullan
        foreach (var entityType in modelBuilder.Model.GetEntityTypes())
        {
            foreach (var property in entityType.GetProperties())
            {
                if (property.ClrType == typeof(Guid) || property.ClrType == typeof(Guid?))
                {
                    property.SetColumnType("uuid");
                }
            }
        }

        // ExchangeRate indexes
        modelBuilder.Entity<ExchangeRate>()
            .HasIndex(er => new { er.BaseCurrency, er.TargetCurrency, er.FetchedAt })
            .HasDatabaseName("IX_ExchangeRate_BaseCurrency_TargetCurrency_FetchedAt");

        modelBuilder.Entity<ExchangeRate>()
            .HasIndex(er => new { er.TargetCurrency, er.FetchedAt })
            .HasDatabaseName("IX_ExchangeRate_TargetCurrency_FetchedAt");
    }
}

