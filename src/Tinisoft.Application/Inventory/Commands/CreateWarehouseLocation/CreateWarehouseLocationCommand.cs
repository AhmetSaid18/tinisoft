using MediatR;

namespace Tinisoft.Application.Inventory.Commands.CreateWarehouseLocation;

public class CreateWarehouseLocationCommand : IRequest<CreateWarehouseLocationResponse>
{
    public Guid WarehouseId { get; set; }
    
    // Lokasyon hiyerarşisi
    public string? Zone { get; set; } // Bölüm (A, B, C, vb.)
    public string? Aisle { get; set; } // Koridor (1, 2, 3, vb.)
    public string? Rack { get; set; } // Raf (1, 2, 3, vb.)
    public string? Shelf { get; set; } // Sıra (1, 2, 3, vb.)
    public string? Level { get; set; } // Katman (1, 2, 3, vb.)
    
    // Lokasyon bilgileri
    public string? Name { get; set; }
    public string? Description { get; set; }
    public decimal? Width { get; set; }
    public decimal? Height { get; set; }
    public decimal? Depth { get; set; }
    public decimal? MaxWeight { get; set; }
}

public class CreateWarehouseLocationResponse
{
    public Guid LocationId { get; set; }
    public string LocationCode { get; set; } = string.Empty;
    public string Message { get; set; } = string.Empty;
}

