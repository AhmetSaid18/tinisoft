namespace Tinisoft.Application.Discounts.Services;

/// <summary>
/// İndirim hesaplaması için cart item bilgisi
/// </summary>
public class CartItemForDiscount
{
    public Guid ProductId { get; set; }
    public List<Guid> CategoryIds { get; set; } = new();
    public decimal TotalPrice { get; set; } // Quantity * UnitPrice
}



