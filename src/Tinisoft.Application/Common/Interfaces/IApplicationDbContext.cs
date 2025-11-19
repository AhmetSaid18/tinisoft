using Microsoft.EntityFrameworkCore;
using Tinisoft.Domain.Entities;

namespace Tinisoft.Application.Common.Interfaces;

public interface IApplicationDbContext
{
    DbSet<Tenant> Tenants { get; }
    DbSet<Plan> Plans { get; }
    DbSet<Domain> Domains { get; }
    DbSet<Template> Templates { get; }
    DbSet<User> Users { get; }
    DbSet<UserTenantRole> UserTenantRoles { get; }
    DbSet<Product> Products { get; }
    DbSet<ProductVariant> ProductVariants { get; }
    DbSet<Category> Categories { get; }
    DbSet<ProductCategory> ProductCategories { get; }
    DbSet<Order> Orders { get; }
    DbSet<OrderItem> OrderItems { get; }
    DbSet<Webhook> Webhooks { get; }
    DbSet<WebhookDelivery> WebhookDeliveries { get; }
    DbSet<AuditLog> AuditLogs { get; }
    DbSet<Warehouse> Warehouses { get; }
    DbSet<ApiKey> ApiKeys { get; }
    DbSet<MarketplaceIntegration> MarketplaceIntegrations { get; }
    DbSet<ProductImage> ProductImages { get; }
    DbSet<ProductOption> ProductOptions { get; }
    DbSet<ProductTag> ProductTags { get; }
    DbSet<ProductMetafield> ProductMetafields { get; }
    DbSet<TaxRate> TaxRates { get; }
    DbSet<TaxRule> TaxRules { get; }
    DbSet<ProductInventory> ProductInventories { get; }
    DbSet<Customer> Customers { get; }
    DbSet<CustomerAddress> CustomerAddresses { get; }
    DbSet<Cart> Carts { get; }
    DbSet<CartItem> CartItems { get; }
    DbSet<Coupon> Coupons { get; }
    DbSet<ProductReview> ProductReviews { get; }
    DbSet<CouponProduct> CouponProducts { get; }
    DbSet<CouponCategory> CouponCategories { get; }
    DbSet<CouponExcludedProduct> CouponExcludedProducts { get; }
    DbSet<CouponCustomer> CouponCustomers { get; }
    DbSet<CouponUsage> CouponUsages { get; }
    DbSet<Reseller> Resellers { get; }
    DbSet<ResellerPrice> ResellerPrices { get; }
    DbSet<ShippingProvider> ShippingProviders { get; }
    DbSet<Shipment> Shipments { get; }
    DbSet<EmailProvider> EmailProviders { get; }
    DbSet<EmailTemplate> EmailTemplates { get; }
    DbSet<EmailNotification> EmailNotifications { get; }
    DbSet<ReviewVote> ReviewVotes { get; }
    DbSet<Invoice> Invoices { get; }
    DbSet<InvoiceItem> InvoiceItems { get; }
    DbSet<TenantInvoiceSettings> TenantInvoiceSettings { get; }
    
    Task<int> SaveChangesAsync(CancellationToken cancellationToken = default);
    DbSet<TEntity> Set<TEntity>() where TEntity : class;
}

