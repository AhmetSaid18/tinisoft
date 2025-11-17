using Tinisoft.Domain.Common;

namespace Tinisoft.Domain.Entities;

public class ProductCategory : BaseEntity
{
    public Guid ProductId { get; set; }
    public Product? Product { get; set; }
    
    public Guid CategoryId { get; set; }
    public Category? Category { get; set; }
    
    public bool IsPrimary { get; set; }
}

