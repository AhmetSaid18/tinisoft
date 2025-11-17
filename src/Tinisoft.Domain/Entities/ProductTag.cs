using Tinisoft.Domain.Common;

namespace Tinisoft.Domain.Entities;

public class ProductTag : BaseEntity, ITenantEntity
{
    public Guid TenantId { get; set; }
    public Tenant? Tenant { get; set; }
    
    public string Name { get; set; } = string.Empty;
    public string Slug { get; set; } = string.Empty;
    
    // Navigation
    public ICollection<Product> Products { get; set; } = new List<Product>();
}

