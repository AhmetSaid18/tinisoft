using MediatR;

namespace Tinisoft.Application.Customers.Queries.GetCart;

public class GetCartQuery : IRequest<GetCartResponse>
{
}

public class GetCartResponse
{
    public Guid CartId { get; set; }
    public List<CartItemDto> Items { get; set; } = new();
    public string? CouponCode { get; set; }
    public string? CouponName { get; set; }
    public decimal Subtotal { get; set; }
    public decimal Tax { get; set; }
    public decimal Shipping { get; set; }
    public decimal Discount { get; set; }
    public decimal Total { get; set; }
    public string Currency { get; set; } = "TRY";
    public DateTime LastUpdatedAt { get; set; }
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
    public string? ProductImageUrl { get; set; }
}

