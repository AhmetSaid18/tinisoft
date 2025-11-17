using MediatR;

namespace Tinisoft.Application.Products.Commands.CreateProduct;

public class CreateProductCommand : IRequest<CreateProductResponse>
{
    // Basic Info
    public string Title { get; set; } = string.Empty;
    public string? Description { get; set; }
    public string? ShortDescription { get; set; }
    public string Slug { get; set; } = string.Empty;
    public string? SKU { get; set; }
    public string? Barcode { get; set; }
    public string? GTIN { get; set; }
    
    // Pricing
    public decimal Price { get; set; }
    public decimal? CompareAtPrice { get; set; }
    public decimal CostPerItem { get; set; }
    public string Currency { get; set; } = "TRY";
    
    // Status
    public string Status { get; set; } = "Draft"; // Draft, Active, Archived
    public bool IsActive { get; set; } = true;
    
    // Inventory
    public bool TrackInventory { get; set; }
    public int? InventoryQuantity { get; set; }
    public bool AllowBackorder { get; set; }
    public string InventoryPolicy { get; set; } = "Deny";
    
    // Physical Properties
    public decimal? Weight { get; set; }
    public string? WeightUnit { get; set; } = "kg";
    public decimal? Length { get; set; }
    public decimal? Width { get; set; }
    public decimal? Height { get; set; }
    
    // Shipping
    public bool RequiresShipping { get; set; } = true;
    public bool IsDigital { get; set; } = false;
    public decimal? ShippingWeight { get; set; }
    
    // Tax
    public bool IsTaxable { get; set; } = true;
    public string? TaxCode { get; set; }
    
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
    
    // Vendor/Type
    public string? Vendor { get; set; }
    public string? ProductType { get; set; }
    
    // Publishing
    public string PublishedScope { get; set; } = "web"; // web, global
    public string? TemplateSuffix { get; set; }
    
    // Gift Card
    public bool IsGiftCard { get; set; } = false;
    
    // Inventory Management
    public string? InventoryManagement { get; set; }
    public string? FulfillmentService { get; set; }
    
    // International Trade
    public string? CountryOfOrigin { get; set; }
    public string? HSCode { get; set; }
    
    // Quantity Rules
    public int? MinQuantity { get; set; }
    public int? MaxQuantity { get; set; }
    public int? IncrementQuantity { get; set; }
    
    // Sales Channels
    public List<string> SalesChannels { get; set; } = new();
    
    // Media
    public string? VideoUrl { get; set; }
    public string? VideoThumbnailUrl { get; set; }
    
    // Custom Fields
    public Dictionary<string, object>? CustomFields { get; set; }
    
    // Inventory Location
    public Guid? DefaultInventoryLocationId { get; set; }
    
    // Barcode
    public string? BarcodeFormat { get; set; }
    
    // Unit Pricing
    public decimal? UnitPrice { get; set; }
    public string? UnitPriceUnit { get; set; }
    
    // Tax Details
    public bool ChargeTaxes { get; set; } = true;
    public string? TaxCategory { get; set; }
    
    // Shipping
    public string? ShippingClass { get; set; }
    
    // Images - Base64 veya URL
    public List<ImageInputDto> Images { get; set; } = new();
    
    // Options (Size, Color, etc.)
    public List<ProductOptionDto> Options { get; set; } = new();
    
    // Metafields (Custom Fields)
    public List<MetafieldDto> Metafields { get; set; } = new();
    
    // Categories, Tags & Collections
    public List<Guid> CategoryIds { get; set; } = new();
    public List<string> Tags { get; set; } = new();
    public List<string> Collections { get; set; } = new();
    
    // Inventory per Warehouse (Depo bazlı stok)
    public List<WarehouseInventoryDto> WarehouseInventories { get; set; } = new();
}

public class WarehouseInventoryDto
{
    public Guid WarehouseId { get; set; }
    public int Quantity { get; set; }
    public int? MinStockLevel { get; set; }
    public int? MaxStockLevel { get; set; }
    public decimal? Cost { get; set; } // Bu depodaki ürünün maliyeti
    public string? Location { get; set; } // Depo içi konum
}

public class ImageInputDto
{
    public string? Base64Data { get; set; } // Base64 encoded image
    public string? Url { get; set; } // External URL
    public string? AltText { get; set; }
    public int Position { get; set; }
    public bool IsFeatured { get; set; }
}

public class ProductOptionDto
{
    public string Name { get; set; } = string.Empty; // Size, Color, etc.
    public List<string> Values { get; set; } = new(); // ["Small", "Medium", "Large"]
    public int Position { get; set; }
}

public class MetafieldDto
{
    public string Namespace { get; set; } = "custom";
    public string Key { get; set; } = string.Empty;
    public string Value { get; set; } = string.Empty;
    public string Type { get; set; } = "single_line_text_field";
    public string? Description { get; set; }
}

public class CreateProductResponse
{
    public Guid ProductId { get; set; }
    public string Title { get; set; } = string.Empty;
}

