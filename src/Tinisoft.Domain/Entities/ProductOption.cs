using Tinisoft.Domain.Common;

namespace Tinisoft.Domain.Entities;

public class ProductOption : BaseEntity
{
    public Guid ProductId { get; set; }
    public Product? Product { get; set; }
    
    public string Name { get; set; } = string.Empty; // Size, Color, Material, etc.
    public int Position { get; set; }
    public List<string> Values { get; set; } = new(); // ["Small", "Medium", "Large"] veya ["Red", "Blue", "Green"]
}

