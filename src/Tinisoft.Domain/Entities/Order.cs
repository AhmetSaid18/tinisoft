using System.Text.Json;
using Tinisoft.Domain.Common;

namespace Tinisoft.Domain.Entities;

public class Order : BaseEntity, ITenantEntity
{
    public Guid TenantId { get; set; }
    public Tenant? Tenant { get; set; }
    
    public string OrderNumber { get; set; } = string.Empty; // Unique per tenant
    public string Status { get; set; } = "Pending"; // Pending, Paid, Processing, Shipped, Delivered, Cancelled
    
    // Customer
    public string CustomerEmail { get; set; } = string.Empty;
    public string? CustomerPhone { get; set; }
    public string? CustomerFirstName { get; set; }
    public string? CustomerLastName { get; set; }
    public Guid? CustomerId { get; set; }
    public Customer? Customer { get; set; }
    
    // Shipping Address
    public string? ShippingAddressLine1 { get; set; }
    public string? ShippingAddressLine2 { get; set; }
    public string? ShippingCity { get; set; }
    public string? ShippingState { get; set; }
    public string? ShippingPostalCode { get; set; }
    public string? ShippingCountry { get; set; }
    
    // Totals (JSON for flexibility)
    public string TotalsJson { get; set; } = "{}"; // {subtotal, tax, shipping, discount, total}
    
    // Payment
    public string? PaymentProvider { get; set; } // PayTR
    public string? PaymentReference { get; set; } // PayTR transaction ID
    public string? PaymentStatus { get; set; } // Pending, Paid, Failed, Refunded
    public DateTime? PaidAt { get; set; }
    
    // Reseller (B2B orders)
    public Guid? ResellerId { get; set; }
    public Reseller? Reseller { get; set; }
    public bool IsResellerOrder { get; set; } = false; // Bayi siparişi mi?
    
    // Coupon
    public string? CouponCode { get; set; } // Kullanılan kupon kodu
    public Guid? CouponId { get; set; }
    public Coupon? Coupon { get; set; }
    
    // Shipping
    public string? ShippingMethod { get; set; }
    public string? TrackingNumber { get; set; }
    public DateTime? ShippedAt { get; set; }
    
    // Invoice
    public Guid? InvoiceId { get; set; }
    public Invoice? Invoice { get; set; }
    
    // Navigation
    public ICollection<OrderItem> OrderItems { get; set; } = new List<OrderItem>();
}

