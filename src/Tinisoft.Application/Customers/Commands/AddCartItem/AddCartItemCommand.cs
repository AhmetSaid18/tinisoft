using MediatR;

namespace Tinisoft.Application.Customers.Commands.AddCartItem;

public class AddCartItemCommand : IRequest<AddCartItemResponse>
{
    public Guid ProductId { get; set; }
    public Guid? ProductVariantId { get; set; }
    public int Quantity { get; set; } = 1;
}

public class AddCartItemResponse
{
    public Guid CartItemId { get; set; }
    public Guid CartId { get; set; }
    public CartItemDto Item { get; set; } = new();
    public decimal CartTotal { get; set; }
}

public class CartItemDto
{
    public Guid Id { get; set; }
    public Guid ProductId { get; set; }
    public Guid? ProductVariantId { get; set; }
    public string Title { get; set; } = string.Empty;
    public string? SKU { get; set; }
    public int Quantity { get; set; }
    public decimal UnitPrice { get; set; }
    public decimal TotalPrice { get; set; }
    public string Currency { get; set; } = "TRY";
}



