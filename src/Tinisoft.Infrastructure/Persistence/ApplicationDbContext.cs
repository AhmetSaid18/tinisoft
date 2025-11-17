using Microsoft.EntityFrameworkCore;
using Tinisoft.Domain.Entities;
using Tinisoft.Domain.Common;
using Finbuckle.MultiTenant;
using Tinisoft.Infrastructure.MultiTenant;

namespace Tinisoft.Infrastructure.Persistence;

public class ApplicationDbContext : MultiTenantDbContext
{
    public ApplicationDbContext(ITenantInfo tenantInfo) : base(tenantInfo)
    {
    }

    public ApplicationDbContext(ITenantInfo tenantInfo, DbContextOptions<ApplicationDbContext> options)
        : base(tenantInfo, options)
    {
    }

    // DbSets
    public DbSet<Tenant> Tenants => Set<Tenant>();
    public DbSet<Plan> Plans => Set<Plan>();
    public DbSet<Domain> Domains => Set<Domain>();
    public DbSet<Template> Templates => Set<Template>();
    public DbSet<User> Users => Set<User>();
    public DbSet<UserTenantRole> UserTenantRoles => Set<UserTenantRole>();
    public DbSet<Product> Products => Set<Product>();
    public DbSet<ProductVariant> ProductVariants => Set<ProductVariant>();
    public DbSet<Category> Categories => Set<Category>();
    public DbSet<ProductCategory> ProductCategories => Set<ProductCategory>();
    public DbSet<Order> Orders => Set<Order>();
    public DbSet<OrderItem> OrderItems => Set<OrderItem>();
    public DbSet<Webhook> Webhooks => Set<Webhook>();
    public DbSet<WebhookDelivery> WebhookDeliveries => Set<WebhookDelivery>();
    public DbSet<AuditLog> AuditLogs => Set<AuditLog>();
    public DbSet<Warehouse> Warehouses => Set<Warehouse>();
    public DbSet<ApiKey> ApiKeys => Set<ApiKey>();
    public DbSet<MarketplaceIntegration> MarketplaceIntegrations => Set<MarketplaceIntegration>();
    public DbSet<ProductImage> ProductImages => Set<ProductImage>();
    public DbSet<ProductOption> ProductOptions => Set<ProductOption>();
    public DbSet<ProductTag> ProductTags => Set<ProductTag>();
    public DbSet<ProductMetafield> ProductMetafields => Set<ProductMetafield>();
    public DbSet<TaxRate> TaxRates => Set<TaxRate>();
    public DbSet<TaxRule> TaxRules => Set<TaxRule>();
    public DbSet<ProductInventory> ProductInventories => Set<ProductInventory>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);

        // Tüm Guid property'ler için PostgreSQL UUID type'ını kullan
        // Bu, güvenlik için önemli - sequential ID'ler yerine UUID kullanıyoruz
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

        // Global query filter for tenant entities
        foreach (var entityType in modelBuilder.Model.GetEntityTypes())
        {
            if (typeof(ITenantEntity).IsAssignableFrom(entityType.ClrType))
            {
                modelBuilder.Entity(entityType.ClrType)
                    .HasIndex(nameof(ITenantEntity.TenantId))
                    .HasDatabaseName($"IX_{entityType.GetTableName()}_TenantId");
            }
        }

        // Indexes
        modelBuilder.Entity<Product>()
            .HasIndex(p => new { p.TenantId, p.Slug })
            .IsUnique();

        modelBuilder.Entity<Order>()
            .HasIndex(o => new { o.TenantId, o.OrderNumber })
            .IsUnique();

        modelBuilder.Entity<Domain>()
            .HasIndex(d => d.Host)
            .IsUnique();

        // Template indexes
        modelBuilder.Entity<Template>()
            .HasIndex(t => new { t.Code, t.Version })
            .IsUnique();

        // Relationships
        modelBuilder.Entity<ProductVariant>()
            .HasOne(pv => pv.Product)
            .WithMany(p => p.Variants)
            .HasForeignKey(pv => pv.ProductId)
            .OnDelete(DeleteBehavior.Cascade);

        modelBuilder.Entity<OrderItem>()
            .HasOne(oi => oi.Order)
            .WithMany(o => o.OrderItems)
            .HasForeignKey(oi => oi.OrderId)
            .OnDelete(DeleteBehavior.Cascade);

        // Product relationships
        modelBuilder.Entity<ProductImage>()
            .HasOne(pi => pi.Product)
            .WithMany(p => p.Images)
            .HasForeignKey(pi => pi.ProductId)
            .OnDelete(DeleteBehavior.Cascade);

        modelBuilder.Entity<ProductOption>()
            .HasOne(po => po.Product)
            .WithMany(p => p.Options)
            .HasForeignKey(po => po.ProductId)
            .OnDelete(DeleteBehavior.Cascade);

        // ProductOption Values as JSON
        modelBuilder.Entity<ProductOption>()
            .Property(po => po.Values)
            .HasConversion(
                v => System.Text.Json.JsonSerializer.Serialize(v, (System.Text.Json.JsonSerializerOptions?)null),
                v => System.Text.Json.JsonSerializer.Deserialize<List<string>>(v, (System.Text.Json.JsonSerializerOptions?)null) ?? new List<string>());

        // Product Tags as JSON
        modelBuilder.Entity<Product>()
            .Property(p => p.Tags)
            .HasConversion(
                v => System.Text.Json.JsonSerializer.Serialize(v, (System.Text.Json.JsonSerializerOptions?)null),
                v => System.Text.Json.JsonSerializer.Deserialize<List<string>>(v, (System.Text.Json.JsonSerializerOptions?)null) ?? new List<string>());

        // Product Collections as JSON
        modelBuilder.Entity<Product>()
            .Property(p => p.Collections)
            .HasConversion(
                v => System.Text.Json.JsonSerializer.Serialize(v, (System.Text.Json.JsonSerializerOptions?)null),
                v => System.Text.Json.JsonSerializer.Deserialize<List<string>>(v, (System.Text.Json.JsonSerializerOptions?)null) ?? new List<string>());

        // Product SalesChannels as JSON
        modelBuilder.Entity<Product>()
            .Property(p => p.SalesChannels)
            .HasConversion(
                v => System.Text.Json.JsonSerializer.Serialize(v, (System.Text.Json.JsonSerializerOptions?)null),
                v => System.Text.Json.JsonSerializer.Deserialize<List<string>>(v, (System.Text.Json.JsonSerializerOptions?)null) ?? new List<string>());

        // ProductMetafield relationship
        modelBuilder.Entity<ProductMetafield>()
            .HasOne(pm => pm.Product)
            .WithMany(p => p.Metafields)
            .HasForeignKey(pm => pm.ProductId)
            .OnDelete(DeleteBehavior.Cascade);

        // Index for metafields
        modelBuilder.Entity<ProductMetafield>()
            .HasIndex(pm => new { pm.ProductId, pm.Namespace, pm.Key })
            .IsUnique();

        // TaxRate relationship
        modelBuilder.Entity<Product>()
            .HasOne(p => p.TaxRate)
            .WithMany()
            .HasForeignKey(p => p.TaxRateId)
            .OnDelete(DeleteBehavior.SetNull);

        // TaxRule relationships
        modelBuilder.Entity<TaxRule>()
            .HasOne(tr => tr.Product)
            .WithMany()
            .HasForeignKey(tr => tr.ProductId)
            .OnDelete(DeleteBehavior.SetNull);

        modelBuilder.Entity<TaxRule>()
            .HasOne(tr => tr.Category)
            .WithMany()
            .HasForeignKey(tr => tr.CategoryId)
            .OnDelete(DeleteBehavior.SetNull);

        modelBuilder.Entity<TaxRule>()
            .HasOne(tr => tr.TaxRate)
            .WithMany()
            .HasForeignKey(tr => tr.TaxRateId)
            .OnDelete(DeleteBehavior.Restrict);

        // Indexes for tax
        modelBuilder.Entity<TaxRate>()
            .HasIndex(tr => new { tr.TenantId, tr.Code })
            .IsUnique();

        // ProductInventory relationships
        modelBuilder.Entity<ProductInventory>()
            .HasOne(pi => pi.Product)
            .WithMany()
            .HasForeignKey(pi => pi.ProductId)
            .OnDelete(DeleteBehavior.Cascade);

        modelBuilder.Entity<ProductInventory>()
            .HasOne(pi => pi.Warehouse)
            .WithMany()
            .HasForeignKey(pi => pi.WarehouseId)
            .OnDelete(DeleteBehavior.Restrict);

        // Unique constraint: Bir ürün bir depoda sadece bir kez olabilir
        modelBuilder.Entity<ProductInventory>()
            .HasIndex(pi => new { pi.ProductId, pi.WarehouseId })
            .IsUnique();

        // Indexes for performance
        modelBuilder.Entity<ProductImage>()
            .HasIndex(pi => new { pi.ProductId, pi.Position });

        modelBuilder.Entity<ProductOption>()
            .HasIndex(po => new { po.ProductId, po.Position });

        // Performance Indexes - Kritik sorgular için
        // Product list queries için
        modelBuilder.Entity<Product>()
            .HasIndex(p => new { p.TenantId, p.IsActive, p.CreatedAt })
            .HasDatabaseName("IX_Product_TenantId_IsActive_CreatedAt");

        // Product search için (Title, SKU, Description)
        modelBuilder.Entity<Product>()
            .HasIndex(p => new { p.TenantId, p.Title })
            .HasDatabaseName("IX_Product_TenantId_Title");

        modelBuilder.Entity<Product>()
            .HasIndex(p => new { p.TenantId, p.SKU })
            .HasFilter("[SKU] IS NOT NULL")
            .HasDatabaseName("IX_Product_TenantId_SKU");

        // Product price sorting için
        modelBuilder.Entity<Product>()
            .HasIndex(p => new { p.TenantId, p.Price })
            .HasDatabaseName("IX_Product_TenantId_Price");

        // Category queries için
        modelBuilder.Entity<Category>()
            .HasIndex(c => new { c.TenantId, c.IsActive, c.ParentId })
            .HasDatabaseName("IX_Category_TenantId_IsActive_ParentId");

        // ProductCategory join için
        modelBuilder.Entity<ProductCategory>()
            .HasIndex(pc => new { pc.CategoryId, pc.ProductId })
            .IsUnique()
            .HasDatabaseName("IX_ProductCategory_CategoryId_ProductId");

        // Order queries için
        modelBuilder.Entity<Order>()
            .HasIndex(o => new { o.TenantId, o.Status, o.CreatedAt })
            .HasDatabaseName("IX_Order_TenantId_Status_CreatedAt");

        // Template queries için
        modelBuilder.Entity<Template>()
            .HasIndex(t => new { t.Code, t.IsActive })
            .HasDatabaseName("IX_Template_Code_IsActive");
    }
}

