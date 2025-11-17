using Tinisoft.Domain.Common;

namespace Tinisoft.Domain.Entities;

public class ProductImage : BaseEntity
{
    public Guid ProductId { get; set; }
    public Product? Product { get; set; }
    
    public int Position { get; set; } // Sıralama
    public string AltText { get; set; } = string.Empty;
    
    // Original image
    public string OriginalUrl { get; set; } = string.Empty;
    public long OriginalSizeBytes { get; set; }
    public int OriginalWidth { get; set; }
    public int OriginalHeight { get; set; }
    
    // Processed sizes
    public string? ThumbnailUrl { get; set; } // 150x150
    public string? SmallUrl { get; set; } // 300x300
    public string? MediumUrl { get; set; } // 600x600
    public string? LargeUrl { get; set; } // 1200x1200
    
    public bool IsFeatured { get; set; }
}

