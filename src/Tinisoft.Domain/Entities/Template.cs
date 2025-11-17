using Tinisoft.Domain.Common;

namespace Tinisoft.Domain.Entities;

public class Template : BaseEntity
{
    public string Code { get; set; } = string.Empty; // "minimal", "fashion", "restaurant"
    public string Name { get; set; } = string.Empty; // "Minimal Tasarım"
    public string Description { get; set; } = string.Empty;
    public int Version { get; set; } = 1; // 1, 2, 3...
    public string? PreviewImageUrl { get; set; } // Önizleme görseli
    public bool IsActive { get; set; } = true;
    
    // Template metadata (JSON - esnek yapı için)
    public string? MetadataJson { get; set; } // {sections: [...], features: [...]}
    
    // Navigation
    public ICollection<Tenant> Tenants { get; set; } = new List<Tenant>();
}

