using Tinisoft.Domain.Common;

namespace Tinisoft.Domain.Entities;

public class Category : BaseEntity, ITenantEntity
{
    public Guid TenantId { get; set; }
    public Tenant? Tenant { get; set; }
    
    public string Name { get; set; } = string.Empty;
    public string Slug { get; set; } = string.Empty;
    public string? Description { get; set; }
    public string? ImageUrl { get; set; }
    
    public Guid? ParentCategoryId { get; set; }
    public Category? ParentCategory { get; set; }
    public ICollection<Category> SubCategories { get; set; } = new List<Category>();
    
    public int DisplayOrder { get; set; }
    public bool IsActive { get; set; } = true;
    
    // Navigation
    public ICollection<ProductCategory> ProductCategories { get; set; } = new List<ProductCategory>();
}

