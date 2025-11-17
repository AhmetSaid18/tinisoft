using Tinisoft.Domain.Common;

namespace Tinisoft.Domain.Entities;

public class ProductVariant : BaseEntity, ITenantEntity
{
    public Guid TenantId { get; set; }
    public Guid ProductId { get; set; }
    public Product? Product { get; set; }
    
    public string Title { get; set; } = string.Empty; // "Small / Red"
    public string? SKU { get; set; }
    
    public decimal Price { get; set; }
    public decimal? CompareAtPrice { get; set; }
    public decimal CostPerItem { get; set; }
    
    public bool TrackInventory { get; set; }
    public int? InventoryQuantity { get; set; }
    
    // Option values (JSON)
    public string? OptionValuesJson { get; set; } // {"Size": "Small", "Color": "Red"}
}

