using MediatR;

namespace Tinisoft.Application.Products.Commands.UpdateProduct;

public class UpdateProductCommand : IRequest<UpdateProductResponse>
{
    public Guid ProductId { get; set; }
    public string? Title { get; set; }
    public string? Description { get; set; }
    public string? Slug { get; set; }
    public string? SKU { get; set; }
    public decimal? Price { get; set; }
    public decimal? CompareAtPrice { get; set; }
    public decimal? CostPerItem { get; set; }
    public bool? TrackInventory { get; set; }
    public int? InventoryQuantity { get; set; }
    public bool? IsActive { get; set; }
    public string? MetaTitle { get; set; }
    public string? MetaDescription { get; set; }
    public string? FeaturedImageUrl { get; set; }
    public List<string>? ImageUrls { get; set; }
}

public class UpdateProductResponse
{
    public Guid ProductId { get; set; }
    public string Title { get; set; } = string.Empty;
}

