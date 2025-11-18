using MediatR;

namespace Tinisoft.Application.Products.Commands.UpdateProduct;

public class UpdateProductCommand : IRequest<UpdateProductResponse>
{
    public Guid ProductId { get; set; }
    public string? Title { get; set; }
    public string? Description { get; set; }
    public string? Slug { get; set; }
    public string? SKU { get; set; }
    public decimal? Price { get; set; } // Satış fiyatı
    public decimal? CompareAtPrice { get; set; }
    public decimal? CostPerItem { get; set; }
    
    // Multi-Currency Support
    public string? PurchaseCurrency { get; set; }
    public decimal? PurchasePrice { get; set; }
    public bool? AutoConvertSalePrice { get; set; }
    public bool? TrackInventory { get; set; }
    public int? InventoryQuantity { get; set; }
    public bool? IsActive { get; set; }
    
    // SEO - React Helmet için meta tag'leri
    public string? MetaTitle { get; set; }
    public string? MetaDescription { get; set; }
    public string? MetaKeywords { get; set; }
    
    // Open Graph
    public string? OgTitle { get; set; }
    public string? OgDescription { get; set; }
    public string? OgImage { get; set; }
    public string? OgType { get; set; }
    
    // Twitter Card
    public string? TwitterCard { get; set; }
    public string? TwitterTitle { get; set; }
    public string? TwitterDescription { get; set; }
    public string? TwitterImage { get; set; }
    
    // Canonical URL
    public string? CanonicalUrl { get; set; }
    
    public string? FeaturedImageUrl { get; set; }
    public List<string>? ImageUrls { get; set; }
}

public class UpdateProductResponse
{
    public Guid ProductId { get; set; }
    public string Title { get; set; } = string.Empty;
}

