using MediatR;

namespace Tinisoft.Application.Inventory.Queries.GetStockLevel;

public class GetStockLevelQuery : IRequest<GetStockLevelResponse>
{
    public Guid ProductId { get; set; }
    public Guid? VariantId { get; set; }
}

public class GetStockLevelResponse
{
    public Guid ProductId { get; set; }
    public Guid? VariantId { get; set; }
    public int? Quantity { get; set; }
    public bool TrackInventory { get; set; }
    public bool IsInStock => TrackInventory && Quantity.HasValue && Quantity > 0;
    public bool IsLowStock { get; set; } // Eğer stok eşiğinin altındaysa
}



