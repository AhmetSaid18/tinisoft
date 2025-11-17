using MediatR;

namespace Tinisoft.Application.Inventory.Commands.AdjustStock;

public class AdjustStockCommand : IRequest<AdjustStockResponse>
{
    public Guid ProductId { get; set; }
    public Guid? VariantId { get; set; }
    public int QuantityChange { get; set; }
    public string Reason { get; set; } = string.Empty; // Restock, Sale, Adjustment, Return, etc.
    public string? Notes { get; set; }
}

public class AdjustStockResponse
{
    public Guid ProductId { get; set; }
    public Guid? VariantId { get; set; }
    public int OldQuantity { get; set; }
    public int NewQuantity { get; set; }
}

