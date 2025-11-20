using MediatR;

namespace Tinisoft.Application.Inventory.Commands.CountInventory;

/// <summary>
/// Stok sayımı (Inventory Count) - Fiziksel sayım sonucu ile sistem stokunu karşılaştır
/// </summary>
public class CountInventoryCommand : IRequest<CountInventoryResponse>
{
    public Guid ProductInventoryId { get; set; }
    public int CountedQuantity { get; set; } // Fiziksel sayım sonucu
    public string? Notes { get; set; }
    public Guid? CountedByUserId { get; set; }
}

public class CountInventoryResponse
{
    public Guid ProductInventoryId { get; set; }
    public int PreviousQuantity { get; set; }
    public int CountedQuantity { get; set; }
    public int Difference { get; set; } // CountedQuantity - PreviousQuantity
    public bool Success { get; set; }
    public string? Message { get; set; }
}



