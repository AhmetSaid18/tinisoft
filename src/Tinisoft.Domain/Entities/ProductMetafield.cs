using Tinisoft.Domain.Common;

namespace Tinisoft.Domain.Entities;

public class ProductMetafield : BaseEntity
{
    public Guid ProductId { get; set; }
    public Product? Product { get; set; }
    
    public string Namespace { get; set; } = string.Empty; // "custom" veya özel namespace
    public string Key { get; set; } = string.Empty; // "size_chart", "care_instructions", etc.
    public string Value { get; set; } = string.Empty; // JSON veya string
    public string Type { get; set; } = "single_line_text_field"; // single_line_text_field, multi_line_text_field, number_integer, etc.
    public string? Description { get; set; }
}

