using Tinisoft.Domain.Common;

namespace Tinisoft.Domain.Entities;

/// <summary>
/// Müşteri sepeti (shopping cart)
/// </summary>
public class Cart : BaseEntity, ITenantEntity
{
    public Guid TenantId { get; set; }
    public Tenant? Tenant { get; set; }

    public Guid CustomerId { get; set; }
    public Customer? Customer { get; set; }

    // Cart Items
    public ICollection<CartItem> Items { get; set; } = new List<CartItem>();

    // Coupon
    public string? CouponCode { get; set; } // Uygulanan kupon kodu
    public Guid? CouponId { get; set; }
    public Coupon? Coupon { get; set; }

    // Totals (calculated)
    public decimal Subtotal { get; set; }
    public decimal Tax { get; set; }
    public decimal Shipping { get; set; }
    public decimal Discount { get; set; }
    public decimal Total { get; set; }
    public string Currency { get; set; } = "TRY";

    public DateTime? ExpiresAt { get; set; } // Sepet süresi doldu mu?
    public DateTime LastUpdatedAt { get; set; } = DateTime.UtcNow;
}

public class CartItem : BaseEntity
{
    public Guid CartId { get; set; }
    public Cart? Cart { get; set; }

    public Guid ProductId { get; set; }
    public Product? Product { get; set; }

    public Guid? ProductVariantId { get; set; }
    public ProductVariant? ProductVariant { get; set; }

    public string Title { get; set; } = string.Empty;
    public string? SKU { get; set; }
    public int Quantity { get; set; }
    public decimal UnitPrice { get; set; }
    public decimal TotalPrice { get; set; }
    public string Currency { get; set; } = "TRY";
}

