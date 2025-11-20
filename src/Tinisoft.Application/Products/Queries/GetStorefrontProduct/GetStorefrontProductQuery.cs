using MediatR;

namespace Tinisoft.Application.Products.Queries.GetStorefrontProduct;

/// <summary>
/// Storefront için public ürün detayı (müşteriler için - tenant'ın seçtiği kura göre fiyat gösterimi)
/// </summary>
public class GetStorefrontProductQuery : IRequest<GetStorefrontProductResponse>
{
    public Guid ProductId { get; set; }
    public string? PreferredCurrency { get; set; } // Müşterinin tercih ettiği para birimi (opsiyonel)
}

public class GetStorefrontProductResponse
{
    public Guid Id { get; set; }
    public string Title { get; set; } = string.Empty;
    public string? Description { get; set; }
    public string? ShortDescription { get; set; }
    public string Slug { get; set; } = string.Empty;
    public string? SKU { get; set; }
    public decimal Price { get; set; } // Tenant'ın seçtiği kura göre dönüştürülmüş fiyat
    public decimal? CompareAtPrice { get; set; }
    public string Currency { get; set; } = "TRY"; // Gösterilen para birimi
    public int? InventoryQuantity { get; set; }
    public bool IsInStock => InventoryQuantity == null || InventoryQuantity > 0;
    public bool AllowBackorder { get; set; }
    public decimal? Weight { get; set; }
    public string? WeightUnit { get; set; }
    public bool RequiresShipping { get; set; }
    public bool IsDigital { get; set; }
    public bool IsTaxable { get; set; }
    public string? MetaTitle { get; set; }
    public string? MetaDescription { get; set; }
    public string? MetaKeywords { get; set; }
    public string? Vendor { get; set; }
    public string? ProductType { get; set; }
    public List<StorefrontImageDto> Images { get; set; } = new();
    public List<StorefrontCategoryDto> Categories { get; set; } = new();
    public List<StorefrontVariantDto> Variants { get; set; } = new();
    public List<StorefrontOptionDto> Options { get; set; } = new();
    public List<string> Tags { get; set; } = new();
    public DateTime CreatedAt { get; set; }
}

public class StorefrontImageDto
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

public class StorefrontCategoryDto
{
    public Guid Id { get; set; }
    public string Name { get; set; } = string.Empty;
    public string Slug { get; set; } = string.Empty;
}

public class StorefrontVariantDto
{
    public Guid Id { get; set; }
    public string Title { get; set; } = string.Empty;
    public string? SKU { get; set; }
    public decimal Price { get; set; }
    public int? InventoryQuantity { get; set; }
    public bool IsInStock => InventoryQuantity == null || InventoryQuantity > 0;
}

public class StorefrontOptionDto
{
    public Guid Id { get; set; }
    public string Name { get; set; } = string.Empty;
    public List<string> Values { get; set; } = new();
    public int Position { get; set; }
}



