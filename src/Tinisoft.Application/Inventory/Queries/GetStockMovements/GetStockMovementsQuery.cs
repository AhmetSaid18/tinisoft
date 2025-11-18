using MediatR;

namespace Tinisoft.Application.Inventory.Queries.GetStockMovements;

/// <summary>
/// Stok hareket geçmişi sorgulama
/// </summary>
public class GetStockMovementsQuery : IRequest<GetStockMovementsResponse>
{
    public Guid? ProductId { get; set; }
    public Guid? WarehouseId { get; set; }
    public Guid? WarehouseLocationId { get; set; }
    public string? MovementType { get; set; } // IN, OUT, TRANSFER, ADJUSTMENT, RESERVED
    public DateTime? FromDate { get; set; }
    public DateTime? ToDate { get; set; }
    public int Page { get; set; } = 1;
    public int PageSize { get; set; } = 50;
}

public class GetStockMovementsResponse
{
    public List<StockMovementDto> Movements { get; set; } = new();
    public int TotalCount { get; set; }
    public int Page { get; set; }
    public int PageSize { get; set; }
    public int TotalPages => (int)Math.Ceiling(TotalCount / (double)PageSize);
}

public class StockMovementDto
{
    public Guid Id { get; set; }
    public Guid ProductId { get; set; }
    public string? ProductTitle { get; set; }
    public string? ProductSKU { get; set; }
    public Guid? ProductVariantId { get; set; }
    public Guid WarehouseId { get; set; }
    public string? WarehouseName { get; set; }
    public Guid? WarehouseLocationId { get; set; }
    public string? LocationCode { get; set; }
    public string MovementType { get; set; } = string.Empty;
    public int Quantity { get; set; }
    public int QuantityBefore { get; set; }
    public int QuantityAfter { get; set; }
    public Guid? ReferenceId { get; set; }
    public string? ReferenceType { get; set; }
    public string? ReferenceNumber { get; set; }
    public string? Reason { get; set; }
    public string? Notes { get; set; }
    public Guid? UserId { get; set; }
    public string? UserName { get; set; }
    public decimal? UnitCost { get; set; }
    public decimal? TotalCost { get; set; }
    public DateTime CreatedAt { get; set; }
}

