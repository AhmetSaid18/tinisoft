using Tinisoft.Domain.Common;

namespace Tinisoft.Domain.Entities;

/// <summary>
/// Kupon/Promosyon kodu
/// </summary>
public class Coupon : BaseEntity, ITenantEntity
{
    public Guid TenantId { get; set; }
    public Tenant? Tenant { get; set; }

    public string Code { get; set; } = string.Empty; // Kupon kodu (örn: "SUMMER2024")
    public string Name { get; set; } = string.Empty; // Kupon adı (örn: "Yaz İndirimi")
    public string? Description { get; set; }

    // Discount Type
    public string DiscountType { get; set; } = "Percentage"; // Percentage, FixedAmount, FreeShipping
    public decimal DiscountValue { get; set; } // İndirim değeri (% veya sabit tutar)
    public string Currency { get; set; } = "TRY"; // FixedAmount için para birimi

    // Conditions
    public decimal? MinOrderAmount { get; set; } // Minimum sipariş tutarı
    public decimal? MaxDiscountAmount { get; set; } // Maksimum indirim tutarı (Percentage için)
    public int? MaxUsageCount { get; set; } // Toplam kullanım limiti (null = sınırsız)
    public int? MaxUsagePerCustomer { get; set; } // Müşteri başına kullanım limiti (null = sınırsız)

    // Validity
    public DateTime? ValidFrom { get; set; } // Geçerlilik başlangıç tarihi
    public DateTime? ValidTo { get; set; } // Geçerlilik bitiş tarihi

    // Product/Category Restrictions
    public bool AppliesToAllProducts { get; set; } = true; // Tüm ürünlere uygulanabilir mi?
    public ICollection<CouponProduct> ApplicableProducts { get; set; } = new List<CouponProduct>(); // Belirli ürünler
    public ICollection<CouponCategory> ApplicableCategories { get; set; } = new List<CouponCategory>(); // Belirli kategoriler
    public ICollection<CouponExcludedProduct> ExcludedProducts { get; set; } = new List<CouponExcludedProduct>(); // Hariç tutulan ürünler

    // Customer Restrictions
    public bool AppliesToAllCustomers { get; set; } = true; // Tüm müşterilere uygulanabilir mi?
    public ICollection<CouponCustomer> ApplicableCustomers { get; set; } = new List<CouponCustomer>(); // Belirli müşteriler

    // Status
    public bool IsActive { get; set; } = true;
    public int UsageCount { get; set; } = 0; // Kullanım sayısı

    // Navigation
    public ICollection<CouponUsage> Usages { get; set; } = new List<CouponUsage>();
    public ICollection<Order> Orders { get; set; } = new List<Order>();
}

/// <summary>
/// Kupon - Ürün ilişkisi (kupon hangi ürünlere uygulanabilir)
/// </summary>
public class CouponProduct : BaseEntity
{
    public Guid CouponId { get; set; }
    public Coupon? Coupon { get; set; }

    public Guid ProductId { get; set; }
    public Product? Product { get; set; }
}

/// <summary>
/// Kupon - Kategori ilişkisi (kupon hangi kategorilere uygulanabilir)
/// </summary>
public class CouponCategory : BaseEntity
{
    public Guid CouponId { get; set; }
    public Coupon? Coupon { get; set; }

    public Guid CategoryId { get; set; }
    public Category? Category { get; set; }
}

/// <summary>
/// Kupon - Hariç tutulan ürün (kupon bu ürünlere uygulanmaz)
/// </summary>
public class CouponExcludedProduct : BaseEntity
{
    public Guid CouponId { get; set; }
    public Coupon? Coupon { get; set; }

    public Guid ProductId { get; set; }
    public Product? Product { get; set; }
}

/// <summary>
/// Kupon - Müşteri ilişkisi (kupon hangi müşterilere uygulanabilir)
/// </summary>
public class CouponCustomer : BaseEntity
{
    public Guid CouponId { get; set; }
    public Coupon? Coupon { get; set; }

    public Guid CustomerId { get; set; }
    public Customer? Customer { get; set; }
}

/// <summary>
/// Kupon kullanım kaydı (hangi müşteri hangi kuponu kullandı)
/// </summary>
public class CouponUsage : BaseEntity, ITenantEntity
{
    public Guid TenantId { get; set; }
    public Tenant? Tenant { get; set; }

    public Guid CouponId { get; set; }
    public Coupon? Coupon { get; set; }

    public Guid? CustomerId { get; set; }
    public Customer? Customer { get; set; }

    public Guid OrderId { get; set; }
    public Order? Order { get; set; }

    public decimal DiscountAmount { get; set; } // Uygulanan indirim tutarı
    public DateTime UsedAt { get; set; } = DateTime.UtcNow;
}

