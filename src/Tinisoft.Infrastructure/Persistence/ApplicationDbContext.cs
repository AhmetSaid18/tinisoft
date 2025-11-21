using Microsoft.EntityFrameworkCore;
using Tinisoft.Domain.Entities;
using Tinisoft.Domain.Common;
using Finbuckle.MultiTenant;
using Tinisoft.Infrastructure.MultiTenant;
using Tinisoft.Application.Common.Interfaces;

namespace Tinisoft.Infrastructure.Persistence;

public class ApplicationDbContext : MultiTenantDbContext, IApplicationDbContext
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
    public DbSet<Tinisoft.Domain.Entities.Domain> Domains => Set<Tinisoft.Domain.Entities.Domain>();
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
    public DbSet<Customer> Customers => Set<Customer>();
    public DbSet<CustomerAddress> CustomerAddresses => Set<CustomerAddress>();
    public DbSet<Cart> Carts => Set<Cart>();
    public DbSet<CartItem> CartItems => Set<CartItem>();
    public DbSet<Coupon> Coupons => Set<Coupon>();
    public DbSet<ProductReview> ProductReviews => Set<ProductReview>();
    public DbSet<CouponProduct> CouponProducts => Set<CouponProduct>();
    public DbSet<CouponCategory> CouponCategories => Set<CouponCategory>();
    public DbSet<CouponExcludedProduct> CouponExcludedProducts => Set<CouponExcludedProduct>();
    public DbSet<CouponCustomer> CouponCustomers => Set<CouponCustomer>();
    public DbSet<CouponUsage> CouponUsages => Set<CouponUsage>();
    public DbSet<Reseller> Resellers => Set<Reseller>();
    public DbSet<ResellerPrice> ResellerPrices => Set<ResellerPrice>();
    public DbSet<ShippingProvider> ShippingProviders => Set<ShippingProvider>();
    public DbSet<Shipment> Shipments => Set<Shipment>();
    public DbSet<EmailProvider> EmailProviders => Set<EmailProvider>();
    public DbSet<EmailTemplate> EmailTemplates => Set<EmailTemplate>();
    public DbSet<EmailNotification> EmailNotifications => Set<EmailNotification>();
    public DbSet<ReviewVote> ReviewVotes => Set<ReviewVote>();
    public DbSet<Invoice> Invoices => Set<Invoice>();
    public DbSet<InvoiceItem> InvoiceItems => Set<InvoiceItem>();
    public DbSet<TenantInvoiceSettings> TenantInvoiceSettings => Set<TenantInvoiceSettings>();
    // ExchangeRate artık GlobalDbContext'te (tenant'a bağlı değil)

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

        modelBuilder.Entity<Tinisoft.Domain.Entities.Domain>()
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
            .HasIndex(c => new { c.TenantId, c.IsActive, c.ParentCategoryId })
            .HasDatabaseName("IX_Category_TenantId_IsActive_ParentCategoryId");

        // ProductCategory join için
        modelBuilder.Entity<ProductCategory>()
            .HasIndex(pc => new { pc.CategoryId, pc.ProductId })
            .IsUnique()
            .HasDatabaseName("IX_ProductCategory_CategoryId_ProductId");

        // Order queries için
        modelBuilder.Entity<Order>()
            .HasIndex(o => new { o.TenantId, o.Status, o.CreatedAt })
            .HasDatabaseName("IX_Order_TenantId_Status_CreatedAt");

        // Order-Reseller relationship
        modelBuilder.Entity<Order>()
            .HasOne(o => o.Reseller)
            .WithMany(r => r.Orders)
            .HasForeignKey(o => o.ResellerId)
            .OnDelete(DeleteBehavior.SetNull);

        // Order-Customer relationship
        modelBuilder.Entity<Order>()
            .HasOne(o => o.Customer)
            .WithMany(c => c.Orders)
            .HasForeignKey(o => o.CustomerId)
            .OnDelete(DeleteBehavior.SetNull);

        // Customer indexes
        modelBuilder.Entity<Customer>()
            .HasIndex(c => new { c.TenantId, c.Email })
            .IsUnique()
            .HasDatabaseName("IX_Customer_TenantId_Email");

        modelBuilder.Entity<Customer>()
            .HasIndex(c => new { c.TenantId, c.IsActive })
            .HasDatabaseName("IX_Customer_TenantId_IsActive");

        // CustomerAddress relationship
        modelBuilder.Entity<CustomerAddress>()
            .HasOne(ca => ca.Customer)
            .WithMany(c => c.Addresses)
            .HasForeignKey(ca => ca.CustomerId)
            .OnDelete(DeleteBehavior.Cascade);

        modelBuilder.Entity<CustomerAddress>()
            .HasIndex(ca => new { ca.CustomerId, ca.IsDefaultShipping })
            .HasDatabaseName("IX_CustomerAddress_CustomerId_IsDefaultShipping");

        modelBuilder.Entity<CustomerAddress>()
            .HasIndex(ca => new { ca.CustomerId, ca.IsDefaultBilling })
            .HasDatabaseName("IX_CustomerAddress_CustomerId_IsDefaultBilling");

        // Template queries için
        modelBuilder.Entity<Template>()
            .HasIndex(t => new { t.Code, t.IsActive })
            .HasDatabaseName("IX_Template_Code_IsActive");

        // Reseller relationships
        modelBuilder.Entity<ResellerPrice>()
            .HasOne(rp => rp.Reseller)
            .WithMany(r => r.ResellerPrices)
            .HasForeignKey(rp => rp.ResellerId)
            .OnDelete(DeleteBehavior.Restrict);

        modelBuilder.Entity<ResellerPrice>()
            .HasOne(rp => rp.Product)
            .WithMany()
            .HasForeignKey(rp => rp.ProductId)
            .OnDelete(DeleteBehavior.Cascade);

        // Reseller indexes
        modelBuilder.Entity<Reseller>()
            .HasIndex(r => new { r.TenantId, r.Email })
            .IsUnique()
            .HasDatabaseName("IX_Reseller_TenantId_Email");

        modelBuilder.Entity<Reseller>()
            .HasIndex(r => new { r.TenantId, r.IsActive })
            .HasDatabaseName("IX_Reseller_TenantId_IsActive");

        // ResellerPrice indexes
        modelBuilder.Entity<ResellerPrice>()
            .HasIndex(rp => new { rp.ResellerId, rp.ProductId, rp.MinQuantity })
            .IsUnique()
            .HasDatabaseName("IX_ResellerPrice_ResellerId_ProductId_MinQuantity");

        modelBuilder.Entity<ResellerPrice>()
            .HasIndex(rp => new { rp.TenantId, rp.ProductId, rp.IsActive })
            .HasDatabaseName("IX_ResellerPrice_TenantId_ProductId_IsActive");

        // Cart relationships
        modelBuilder.Entity<Cart>()
            .HasOne(c => c.Customer)
            .WithMany()
            .HasForeignKey(c => c.CustomerId)
            .OnDelete(DeleteBehavior.Cascade);

        modelBuilder.Entity<CartItem>()
            .HasOne(ci => ci.Cart)
            .WithMany(c => c.Items)
            .HasForeignKey(ci => ci.CartId)
            .OnDelete(DeleteBehavior.Cascade);

        modelBuilder.Entity<CartItem>()
            .HasOne(ci => ci.Product)
            .WithMany()
            .HasForeignKey(ci => ci.ProductId)
            .OnDelete(DeleteBehavior.Restrict);

        modelBuilder.Entity<CartItem>()
            .HasOne(ci => ci.ProductVariant)
            .WithMany()
            .HasForeignKey(ci => ci.ProductVariantId)
            .OnDelete(DeleteBehavior.Restrict);

        // Cart indexes
        modelBuilder.Entity<Cart>()
            .HasIndex(c => new { c.TenantId, c.CustomerId })
            .IsUnique()
            .HasDatabaseName("IX_Cart_TenantId_CustomerId");

        modelBuilder.Entity<CartItem>()
            .HasIndex(ci => new { ci.CartId, ci.ProductId, ci.ProductVariantId })
            .IsUnique()
            .HasDatabaseName("IX_CartItem_CartId_ProductId_ProductVariantId");

        // Cart-Coupon relationship
        modelBuilder.Entity<Cart>()
            .HasOne(c => c.Coupon)
            .WithMany()
            .HasForeignKey(c => c.CouponId)
            .OnDelete(DeleteBehavior.SetNull);

        // Order-Coupon relationship
        modelBuilder.Entity<Order>()
            .HasOne(o => o.Coupon)
            .WithMany(c => c.Orders)
            .HasForeignKey(o => o.CouponId)
            .OnDelete(DeleteBehavior.SetNull);

        // Coupon relationships
        modelBuilder.Entity<CouponProduct>()
            .HasOne(cp => cp.Coupon)
            .WithMany(c => c.ApplicableProducts)
            .HasForeignKey(cp => cp.CouponId)
            .OnDelete(DeleteBehavior.Cascade);

        modelBuilder.Entity<CouponProduct>()
            .HasOne(cp => cp.Product)
            .WithMany()
            .HasForeignKey(cp => cp.ProductId)
            .OnDelete(DeleteBehavior.Restrict);

        modelBuilder.Entity<CouponCategory>()
            .HasOne(cc => cc.Coupon)
            .WithMany(c => c.ApplicableCategories)
            .HasForeignKey(cc => cc.CouponId)
            .OnDelete(DeleteBehavior.Cascade);

        modelBuilder.Entity<CouponCategory>()
            .HasOne(cc => cc.Category)
            .WithMany()
            .HasForeignKey(cc => cc.CategoryId)
            .OnDelete(DeleteBehavior.Restrict);

        modelBuilder.Entity<CouponExcludedProduct>()
            .HasOne(cep => cep.Coupon)
            .WithMany(c => c.ExcludedProducts)
            .HasForeignKey(cep => cep.CouponId)
            .OnDelete(DeleteBehavior.Cascade);

        modelBuilder.Entity<CouponExcludedProduct>()
            .HasOne(cep => cep.Product)
            .WithMany()
            .HasForeignKey(cep => cep.ProductId)
            .OnDelete(DeleteBehavior.Restrict);

        modelBuilder.Entity<CouponCustomer>()
            .HasOne(cc => cc.Coupon)
            .WithMany(c => c.ApplicableCustomers)
            .HasForeignKey(cc => cc.CouponId)
            .OnDelete(DeleteBehavior.Cascade);

        modelBuilder.Entity<CouponCustomer>()
            .HasOne(cc => cc.Customer)
            .WithMany()
            .HasForeignKey(cc => cc.CustomerId)
            .OnDelete(DeleteBehavior.Restrict);

        modelBuilder.Entity<CouponUsage>()
            .HasOne(cu => cu.Coupon)
            .WithMany(c => c.Usages)
            .HasForeignKey(cu => cu.CouponId)
            .OnDelete(DeleteBehavior.Restrict);

        modelBuilder.Entity<CouponUsage>()
            .HasOne(cu => cu.Customer)
            .WithMany()
            .HasForeignKey(cu => cu.CustomerId)
            .OnDelete(DeleteBehavior.SetNull);

        modelBuilder.Entity<CouponUsage>()
            .HasOne(cu => cu.Order)
            .WithMany()
            .HasForeignKey(cu => cu.OrderId)
            .OnDelete(DeleteBehavior.Restrict);

        // Coupon indexes
        modelBuilder.Entity<Coupon>()
            .HasIndex(c => new { c.TenantId, c.Code })
            .IsUnique()
            .HasDatabaseName("IX_Coupon_TenantId_Code");

        modelBuilder.Entity<Coupon>()
            .HasIndex(c => new { c.TenantId, c.IsActive, c.ValidFrom, c.ValidTo })
            .HasDatabaseName("IX_Coupon_TenantId_IsActive_ValidFrom_ValidTo");

        modelBuilder.Entity<CouponUsage>()
            .HasIndex(cu => new { cu.CouponId, cu.CustomerId })
            .HasDatabaseName("IX_CouponUsage_CouponId_CustomerId");

        modelBuilder.Entity<CouponUsage>()
            .HasIndex(cu => new { cu.TenantId, cu.UsedAt })
            .HasDatabaseName("IX_CouponUsage_TenantId_UsedAt");

        // ShippingProvider relationships
        modelBuilder.Entity<ShippingProvider>()
            .HasOne(sp => sp.Tenant)
            .WithMany()
            .HasForeignKey(sp => sp.TenantId)
            .OnDelete(DeleteBehavior.Restrict);

        // ShippingProvider indexes
        modelBuilder.Entity<ShippingProvider>()
            .HasIndex(sp => new { sp.TenantId, sp.ProviderCode })
            .IsUnique()
            .HasDatabaseName("IX_ShippingProvider_TenantId_ProviderCode");

        modelBuilder.Entity<ShippingProvider>()
            .HasIndex(sp => new { sp.TenantId, sp.IsActive, sp.IsDefault })
            .HasDatabaseName("IX_ShippingProvider_TenantId_IsActive_IsDefault");

        // Shipment relationships
        modelBuilder.Entity<Shipment>()
            .HasOne(s => s.Order)
            .WithMany()
            .HasForeignKey(s => s.OrderId)
            .OnDelete(DeleteBehavior.Restrict);

        modelBuilder.Entity<Shipment>()
            .HasOne(s => s.ShippingProvider)
            .WithMany()
            .HasForeignKey(s => s.ShippingProviderId)
            .OnDelete(DeleteBehavior.Restrict);

        // Shipment indexes
        modelBuilder.Entity<Shipment>()
            .HasIndex(s => new { s.TenantId, s.OrderId })
            .HasDatabaseName("IX_Shipment_TenantId_OrderId");

        modelBuilder.Entity<Shipment>()
            .HasIndex(s => new { s.TenantId, s.TrackingNumber })
            .IsUnique()
            .HasDatabaseName("IX_Shipment_TenantId_TrackingNumber");

        modelBuilder.Entity<Shipment>()
            .HasIndex(s => new { s.TenantId, s.Status, s.ShippedAt })
            .HasDatabaseName("IX_Shipment_TenantId_Status_ShippedAt");

        // EmailProvider relationships
        modelBuilder.Entity<EmailProvider>()
            .HasOne(ep => ep.Tenant)
            .WithMany()
            .HasForeignKey(ep => ep.TenantId)
            .OnDelete(DeleteBehavior.Restrict);

        // EmailProvider indexes
        modelBuilder.Entity<EmailProvider>()
            .HasIndex(ep => new { ep.TenantId, ep.IsActive, ep.IsDefault })
            .HasDatabaseName("IX_EmailProvider_TenantId_IsActive_IsDefault");

        // EmailTemplate relationships
        modelBuilder.Entity<EmailTemplate>()
            .HasOne(et => et.Tenant)
            .WithMany()
            .HasForeignKey(et => et.TenantId)
            .OnDelete(DeleteBehavior.Restrict);

        // EmailTemplate indexes
        modelBuilder.Entity<EmailTemplate>()
            .HasIndex(et => new { et.TenantId, et.TemplateCode })
            .IsUnique()
            .HasDatabaseName("IX_EmailTemplate_TenantId_TemplateCode");

        // EmailNotification relationships
        modelBuilder.Entity<EmailNotification>()
            .HasOne(en => en.EmailProvider)
            .WithMany()
            .HasForeignKey(en => en.EmailProviderId)
            .OnDelete(DeleteBehavior.SetNull);

        modelBuilder.Entity<EmailNotification>()
            .HasOne(en => en.EmailTemplate)
            .WithMany()
            .HasForeignKey(en => en.EmailTemplateId)
            .OnDelete(DeleteBehavior.SetNull);

        // EmailNotification indexes
        modelBuilder.Entity<EmailNotification>()
            .HasIndex(en => new { en.TenantId, en.Status, en.CreatedAt })
            .HasDatabaseName("IX_EmailNotification_TenantId_Status_CreatedAt");

        modelBuilder.Entity<EmailNotification>()
            .HasIndex(en => new { en.TenantId, en.ToEmail, en.CreatedAt })
            .HasDatabaseName("IX_EmailNotification_TenantId_ToEmail_CreatedAt");

        modelBuilder.Entity<EmailNotification>()
            .HasIndex(en => new { en.ReferenceType, en.ReferenceId })
            .HasDatabaseName("IX_EmailNotification_ReferenceType_ReferenceId");

        // ProductReview relationships
        modelBuilder.Entity<ProductReview>()
            .HasOne(pr => pr.Product)
            .WithMany()
            .HasForeignKey(pr => pr.ProductId)
            .OnDelete(DeleteBehavior.Cascade);

        modelBuilder.Entity<ProductReview>()
            .HasOne(pr => pr.Customer)
            .WithMany()
            .HasForeignKey(pr => pr.CustomerId)
            .OnDelete(DeleteBehavior.SetNull);

        modelBuilder.Entity<ProductReview>()
            .HasOne(pr => pr.Order)
            .WithMany()
            .HasForeignKey(pr => pr.OrderId)
            .OnDelete(DeleteBehavior.SetNull);

        // ProductReview ImageUrls as JSON
        modelBuilder.Entity<ProductReview>()
            .Property(pr => pr.ImageUrls)
            .HasConversion(
                v => System.Text.Json.JsonSerializer.Serialize(v, (System.Text.Json.JsonSerializerOptions?)null),
                v => System.Text.Json.JsonSerializer.Deserialize<List<string>>(v, (System.Text.Json.JsonSerializerOptions?)null) ?? new List<string>());

        // ProductReview indexes
        modelBuilder.Entity<ProductReview>()
            .HasIndex(pr => new { pr.TenantId, pr.ProductId, pr.IsPublished })
            .HasDatabaseName("IX_ProductReview_TenantId_ProductId_IsPublished");

        modelBuilder.Entity<ProductReview>()
            .HasIndex(pr => new { pr.TenantId, pr.ProductId, pr.Rating })
            .HasDatabaseName("IX_ProductReview_TenantId_ProductId_Rating");

        modelBuilder.Entity<ProductReview>()
            .HasIndex(pr => new { pr.TenantId, pr.CustomerId })
            .HasDatabaseName("IX_ProductReview_TenantId_CustomerId");

        modelBuilder.Entity<ProductReview>()
            .HasIndex(pr => new { pr.TenantId, pr.IsApproved, pr.IsPublished, pr.CreatedAt })
            .HasDatabaseName("IX_ProductReview_TenantId_IsApproved_IsPublished_CreatedAt");

        // ReviewVote relationships
        modelBuilder.Entity<ReviewVote>()
            .HasOne(rv => rv.Review)
            .WithMany()
            .HasForeignKey(rv => rv.ReviewId)
            .OnDelete(DeleteBehavior.Cascade);

        modelBuilder.Entity<ReviewVote>()
            .HasOne(rv => rv.Customer)
            .WithMany()
            .HasForeignKey(rv => rv.CustomerId)
            .OnDelete(DeleteBehavior.SetNull);

        // ReviewVote indexes - Duplicate vote önlemek için unique constraint
        modelBuilder.Entity<ReviewVote>()
            .HasIndex(rv => new { rv.TenantId, rv.ReviewId, rv.CustomerId })
            .HasDatabaseName("IX_ReviewVote_TenantId_ReviewId_CustomerId")
            .HasFilter("[CustomerId] IS NOT NULL");

        modelBuilder.Entity<ReviewVote>()
            .HasIndex(rv => new { rv.TenantId, rv.ReviewId, rv.IpAddress })
            .HasDatabaseName("IX_ReviewVote_TenantId_ReviewId_IpAddress")
            .HasFilter("[IpAddress] IS NOT NULL");

        // Invoice relationships
        modelBuilder.Entity<Invoice>()
            .HasOne(i => i.Order)
            .WithMany()
            .HasForeignKey(i => i.OrderId)
            .OnDelete(DeleteBehavior.Restrict);

        // InvoiceItem relationships
        modelBuilder.Entity<InvoiceItem>()
            .HasOne(ii => ii.Invoice)
            .WithMany(i => i.Items)
            .HasForeignKey(ii => ii.InvoiceId)
            .OnDelete(DeleteBehavior.Cascade);

        modelBuilder.Entity<InvoiceItem>()
            .HasOne(ii => ii.Product)
            .WithMany()
            .HasForeignKey(ii => ii.ProductId)
            .OnDelete(DeleteBehavior.Restrict);

        modelBuilder.Entity<InvoiceItem>()
            .HasOne(ii => ii.ProductVariant)
            .WithMany()
            .HasForeignKey(ii => ii.ProductVariantId)
            .OnDelete(DeleteBehavior.SetNull);

        modelBuilder.Entity<InvoiceItem>()
            .HasOne(ii => ii.TaxRate)
            .WithMany()
            .HasForeignKey(ii => ii.TaxRateId)
            .OnDelete(DeleteBehavior.SetNull);

        // TenantInvoiceSettings relationships
        modelBuilder.Entity<TenantInvoiceSettings>()
            .HasOne(tis => tis.Tenant)
            .WithMany()
            .HasForeignKey(tis => tis.TenantId)
            .OnDelete(DeleteBehavior.Restrict);

        // Invoice indexes
        modelBuilder.Entity<Invoice>()
            .HasIndex(i => new { i.TenantId, i.InvoiceNumber, i.InvoiceSerial })
            .IsUnique()
            .HasDatabaseName("IX_Invoice_TenantId_InvoiceNumber_InvoiceSerial");

        modelBuilder.Entity<Invoice>()
            .HasIndex(i => new { i.TenantId, i.OrderId })
            .HasDatabaseName("IX_Invoice_TenantId_OrderId");

        modelBuilder.Entity<Invoice>()
            .HasIndex(i => new { i.TenantId, i.Status, i.InvoiceDate })
            .HasDatabaseName("IX_Invoice_TenantId_Status_InvoiceDate");

        modelBuilder.Entity<Invoice>()
            .HasIndex(i => new { i.TenantId, i.GIBInvoiceId })
            .HasFilter("\"GIBInvoiceId\" IS NOT NULL")
            .HasDatabaseName("IX_Invoice_TenantId_GIBInvoiceId");

        // TenantInvoiceSettings indexes
        modelBuilder.Entity<TenantInvoiceSettings>()
            .HasIndex(tis => new { tis.TenantId })
            .IsUnique()
            .HasDatabaseName("IX_TenantInvoiceSettings_TenantId");
    }
}


