using MediatR;

namespace Tinisoft.Application.Products.Queries.GetProduct;

public class GetProductQuery : IRequest<GetProductResponse>
{
    public Guid ProductId { get; set; }
}

public class GetProductResponse
{
    public Guid Id { get; set; }
    public string Title { get; set; } = string.Empty;
    public string? Description { get; set; }
    public string? ShortDescription { get; set; }
    public string Slug { get; set; } = string.Empty;
    public string? SKU { get; set; }
    public string? Barcode { get; set; }
    public string? GTIN { get; set; }
    public decimal Price { get; set; }
    public decimal? CompareAtPrice { get; set; }
    public decimal CostPerItem { get; set; }
    public string Currency { get; set; } = "TRY";
    public string Status { get; set; } = "Draft";
    public bool TrackInventory { get; set; }
    public int? InventoryQuantity { get; set; }
    public bool AllowBackorder { get; set; }
    public decimal? Weight { get; set; }
    public string? WeightUnit { get; set; }
    public decimal? Length { get; set; }
    public decimal? Width { get; set; }
    public decimal? Height { get; set; }
    public bool RequiresShipping { get; set; }
    public bool IsDigital { get; set; }
    public bool IsTaxable { get; set; }
    public string? TaxCode { get; set; }
    public string? MetaTitle { get; set; }
    public string? MetaDescription { get; set; }
    public string? MetaKeywords { get; set; }
    public string? Vendor { get; set; }
    public string? ProductType { get; set; }
    public string PublishedScope { get; set; } = "web";
    public string? TemplateSuffix { get; set; }
    public bool IsGiftCard { get; set; }
    public string? InventoryManagement { get; set; }
    public string? FulfillmentService { get; set; }
    public string? CountryOfOrigin { get; set; }
    public string? HSCode { get; set; }
    public int? MinQuantity { get; set; }
    public int? MaxQuantity { get; set; }
    public int? IncrementQuantity { get; set; }
    public string? ShippingClass { get; set; }
    public string? BarcodeFormat { get; set; }
    public decimal? UnitPrice { get; set; }
    public string? UnitPriceUnit { get; set; }
    public bool ChargeTaxes { get; set; }
    public string? TaxCategory { get; set; }
    public Guid? DefaultInventoryLocationId { get; set; }
    public bool IsActive { get; set; }
    public DateTime? PublishedAt { get; set; }
    public List<ImageDto> Images { get; set; } = new();
    public List<CategoryDto> Categories { get; set; } = new();
    public List<VariantDto> Variants { get; set; } = new();
    public List<OptionDto> Options { get; set; } = new();
    public List<MetafieldDto> Metafields { get; set; } = new();
    public List<string> Tags { get; set; } = new();
    public List<string> Collections { get; set; } = new();
    public List<string> SalesChannels { get; set; } = new();
    public string? VideoUrl { get; set; }
    public string? VideoThumbnailUrl { get; set; }
    public Dictionary<string, object>? CustomFields { get; set; }
    public DateTime CreatedAt { get; set; }
    public DateTime? UpdatedAt { get; set; }
}

public class ImageDto
{
    public Guid Id { get; set; }
    public string OriginalUrl { get; set; } = string.Empty;
    public string? ThumbnailUrl { get; set; }
    public string? SmallUrl { get; set; }
    public string? MediumUrl { get; set; }
    public string? LargeUrl { get; set; }
    public string AltText { get; set; } = string.Empty;
    public int Position { get; set; }
    public bool IsFeatured { get; set; }
}

public class OptionDto
{
    public Guid Id { get; set; }
    public string Name { get; set; } = string.Empty;
    public List<string> Values { get; set; } = new();
    public int Position { get; set; }
}

public class MetafieldDto
{
    public Guid Id { get; set; }
    public string Namespace { get; set; } = string.Empty;
    public string Key { get; set; } = string.Empty;
    public string Value { get; set; } = string.Empty;
    public string Type { get; set; } = string.Empty;
    public string? Description { get; set; }
}

public class CategoryDto
{
    public Guid Id { get; set; }
    public string Name { get; set; } = string.Empty;
    public string Slug { get; set; } = string.Empty;
}

public class VariantDto
{
    public Guid Id { get; set; }
    public string Title { get; set; } = string.Empty;
    public string? SKU { get; set; }
    public decimal Price { get; set; }
    public int? InventoryQuantity { get; set; }
}

