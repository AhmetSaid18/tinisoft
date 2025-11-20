using Microsoft.EntityFrameworkCore;

namespace Tinisoft.Application.Common.Interfaces;

public interface IApplicationDbContext
{
    DbSet<Entities.Tenant> Tenants { get; }
    DbSet<Entities.Plan> Plans { get; }
    DbSet<Entities.Domain> Domains { get; }
    DbSet<Entities.Template> Templates { get; }
    DbSet<Entities.User> Users { get; }
    DbSet<Entities.UserTenantRole> UserTenantRoles { get; }
    DbSet<Entities.Product> Products { get; }
    DbSet<Entities.ProductVariant> ProductVariants { get; }
    DbSet<Entities.Category> Categories { get; }
    DbSet<Entities.ProductCategory> ProductCategories { get; }
    DbSet<Entities.Order> Orders { get; }
    DbSet<Entities.OrderItem> OrderItems { get; }
    DbSet<Entities.Webhook> Webhooks { get; }
    DbSet<Entities.WebhookDelivery> WebhookDeliveries { get; }
    DbSet<Entities.AuditLog> AuditLogs { get; }
    DbSet<Entities.Warehouse> Warehouses { get; }
    DbSet<Entities.ApiKey> ApiKeys { get; }
    DbSet<Entities.MarketplaceIntegration> MarketplaceIntegrations { get; }
    DbSet<Entities.ProductImage> ProductImages { get; }
    DbSet<Entities.ProductOption> ProductOptions { get; }
    DbSet<Entities.ProductTag> ProductTags { get; }
    DbSet<Entities.ProductMetafield> ProductMetafields { get; }
    DbSet<Entities.TaxRate> TaxRates { get; }
    DbSet<Entities.TaxRule> TaxRules { get; }
    DbSet<Entities.ProductInventory> ProductInventories { get; }
    DbSet<Entities.Customer> Customers { get; }
    DbSet<Entities.CustomerAddress> CustomerAddresses { get; }
    DbSet<Entities.Cart> Carts { get; }
    DbSet<Entities.CartItem> CartItems { get; }
    DbSet<Entities.Coupon> Coupons { get; }
    DbSet<Entities.ProductReview> ProductReviews { get; }
    DbSet<Entities.CouponProduct> CouponProducts { get; }
    DbSet<Entities.CouponCategory> CouponCategories { get; }
    DbSet<Entities.CouponExcludedProduct> CouponExcludedProducts { get; }
    DbSet<Entities.CouponCustomer> CouponCustomers { get; }
    DbSet<Entities.CouponUsage> CouponUsages { get; }
    DbSet<Entities.Reseller> Resellers { get; }
    DbSet<Entities.ResellerPrice> ResellerPrices { get; }
    DbSet<Entities.ShippingProvider> ShippingProviders { get; }
    DbSet<Entities.Shipment> Shipments { get; }
    DbSet<Entities.EmailProvider> EmailProviders { get; }
    DbSet<Entities.EmailTemplate> EmailTemplates { get; }
    DbSet<Entities.EmailNotification> EmailNotifications { get; }
    DbSet<Entities.ReviewVote> ReviewVotes { get; }
    DbSet<Entities.Invoice> Invoices { get; }
    DbSet<Entities.InvoiceItem> InvoiceItems { get; }
    DbSet<Entities.TenantInvoiceSettings> TenantInvoiceSettings { get; }

    Task<int> SaveChangesAsync(CancellationToken cancellationToken = default);
    DbSet<TEntity> Set<TEntity>() where TEntity : class;
    Microsoft.EntityFrameworkCore.ChangeTracking.EntityEntry<TEntity> Entry<TEntity>(TEntity entity) where TEntity : class;
}
