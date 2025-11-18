using Tinisoft.Domain.Common;

namespace Tinisoft.Domain.Entities;

public class Product : BaseEntity, ITenantEntity
{
    public Guid TenantId { get; set; }
    public Tenant? Tenant { get; set; }
    
    // Basic Info
    public string Title { get; set; } = string.Empty;
    public string? Description { get; set; }
    public string? ShortDescription { get; set; }
    public string Slug { get; set; } = string.Empty;
    public string? SKU { get; set; }
    public string? Barcode { get; set; }
    public string? GTIN { get; set; } // Global Trade Item Number
    
    // Pricing
    public decimal Price { get; set; } // Satış fiyatı (sitede gösterilecek)
    public decimal? CompareAtPrice { get; set; }
    public decimal CostPerItem { get; set; }
    public string Currency { get; set; } = "TRY"; // Satış para birimi (sitede gösterilecek)
    
    // Multi-Currency Support
    public string? PurchaseCurrency { get; set; } // Giriş para birimi (EUR, USD, etc.)
    public decimal? PurchasePrice { get; set; } // Giriş fiyatı (EUR/USD olarak girilen)
    public bool AutoConvertSalePrice { get; set; } = true; // Otomatik TL'ye çevir mi?
    public decimal? ExchangeRateAtPurchase { get; set; } // Giriş anındaki kur (audit için)
    
    // Status
    public string Status { get; set; } = "Draft"; // Draft, Active, Archived
    public bool IsActive { get; set; } = true;
    public DateTime? PublishedAt { get; set; }
    
    // Inventory
    public bool TrackInventory { get; set; }
    public int? InventoryQuantity { get; set; }
    public bool AllowBackorder { get; set; } // Stok bitince de satışa izin ver
    public string InventoryPolicy { get; set; } = "Deny"; // Deny, Continue
    
    // Physical Properties
    public decimal? Weight { get; set; } // kg
    public string? WeightUnit { get; set; } = "kg";
    public decimal? Length { get; set; } // cm
    public decimal? Width { get; set; } // cm
    public decimal? Height { get; set; } // cm
    
    // Shipping (moved down - duplicate removed)
    public decimal? ShippingWeight { get; set; }
    public string? ShippingClass { get; set; } // "standard", "express", "fragile", etc.
    
    // Tax (moved down - duplicate removed)
    public bool IsTaxable { get; set; } = true;
    public string? TaxCode { get; set; } // KDV kodu
    
    // SEO - React Helmet için meta tag'leri
    public string? MetaTitle { get; set; } // <title> tag'i için
    public string? MetaDescription { get; set; } // <meta name="description">
    public string? MetaKeywords { get; set; } // <meta name="keywords">
    
    // Open Graph (Facebook, LinkedIn paylaşımları için)
    public string? OgTitle { get; set; } // <meta property="og:title">
    public string? OgDescription { get; set; } // <meta property="og:description">
    public string? OgImage { get; set; } // <meta property="og:image">
    public string? OgType { get; set; } = "product"; // <meta property="og:type">
    
    // Twitter Card
    public string? TwitterCard { get; set; } = "summary_large_image"; // <meta name="twitter:card">
    public string? TwitterTitle { get; set; } // <meta name="twitter:title">
    public string? TwitterDescription { get; set; } // <meta name="twitter:description">
    public string? TwitterImage { get; set; } // <meta name="twitter:image">
    
    // Canonical URL (SEO için)
    public string? CanonicalUrl { get; set; } // <link rel="canonical">
    
    // Vendor/Supplier
    public string? Vendor { get; set; }
    public string? ProductType { get; set; } // T-Shirt, Book, etc.
    
    // Collections/Tags
    public List<string> Tags { get; set; } = new();
    public List<string> Collections { get; set; } = new(); // Koleksiyon slug'ları
    
    // Publishing
    public string PublishedScope { get; set; } = "web"; // web, global
    public string? TemplateSuffix { get; set; } // Tema şablonu
    
    // Gift Card
    public bool IsGiftCard { get; set; } = false;
    
    // Inventory Management
    public string? InventoryManagement { get; set; } // "shopify", "not_managed", custom service
    public string? FulfillmentService { get; set; } // "manual", "amazon", custom
    
    // International Trade
    public string? CountryOfOrigin { get; set; } // ISO country code
    public string? HSCode { get; set; } // Harmonized System Code (gümrük)
    
    // Quantity Rules
    public int? MinQuantity { get; set; } // Minimum sipariş miktarı
    public int? MaxQuantity { get; set; } // Maksimum sipariş miktarı
    public int? IncrementQuantity { get; set; } // Artış miktarı (örn: 2'şer satılır)
    
    // Sales Channels
    public List<string> SalesChannels { get; set; } = new(); // ["online", "pos", "mobile", "marketplace"]
    
    // Media
    public string? VideoUrl { get; set; } // YouTube, Vimeo, etc.
    public string? VideoThumbnailUrl { get; set; }
    
    // Custom Fields (JSON for flexible data)
    public string? CustomFieldsJson { get; set; } // Özel alanlar için JSON
    
    // Inventory Location
    public Guid? DefaultInventoryLocationId { get; set; } // Varsayılan depo
    
    // Barcode
    public string? BarcodeFormat { get; set; } // "UPC", "EAN", "ISBN", etc.
    
    // Unit Pricing
    public decimal? UnitPrice { get; set; } // Birim fiyat
    public string? UnitPriceUnit { get; set; } // "kg", "lt", "m", etc.
    
    // Tax Details
    public bool ChargeTaxes { get; set; } = true;
    public string? TaxCategory { get; set; } // "physical_goods", "digital_goods", "service", etc.
    public Guid? TaxRateId { get; set; } // Varsayılan vergi oranı
    public TaxRate? TaxRate { get; set; }
    
    // Fulfillment
    public string? FulfillmentStatus { get; set; } // "fulfilled", "partial", "unfulfilled"
    public bool RequiresShipping { get; set; } = true;
    public bool IsDigital { get; set; } = false;
    
    // Navigation
    public ICollection<ProductVariant> Variants { get; set; } = new List<ProductVariant>();
    public ICollection<ProductCategory> ProductCategories { get; set; } = new List<ProductCategory>();
    public ICollection<ProductImage> Images { get; set; } = new List<ProductImage>();
    public ICollection<ProductOption> Options { get; set; } = new List<ProductOption>();
    public ICollection<ProductMetafield> Metafields { get; set; } = new List<ProductMetafield>();
    public ICollection<ProductReview> Reviews { get; set; } = new List<ProductReview>();
}

