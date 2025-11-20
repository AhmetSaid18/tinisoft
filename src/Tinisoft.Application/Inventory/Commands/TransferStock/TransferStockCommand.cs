using MediatR;

namespace Tinisoft.Application.Inventory.Commands.TransferStock;

public class TransferStockCommand : IRequest<TransferStockResponse>
{
    public Guid ProductId { get; set; }
    public Guid? ProductVariantId { get; set; }
    
    // Kaynak
    public Guid FromWarehouseId { get; set; }
    public Guid? FromWarehouseLocationId { get; set; }
    
    // Hedef
    public Guid ToWarehouseId { get; set; }
    public Guid? ToWarehouseLocationId { get; set; }
    
    public int Quantity { get; set; }
    public string? Reason { get; set; }
    public string? Notes { get; set; }
    public Guid? UserId { get; set; } // Transferi yapan kullanıcı
}

public class TransferStockResponse
{
    public bool Success { get; set; }
    public string? Message { get; set; }
    public Guid? FromInventoryId { get; set; }
    public Guid? ToInventoryId { get; set; }
}



