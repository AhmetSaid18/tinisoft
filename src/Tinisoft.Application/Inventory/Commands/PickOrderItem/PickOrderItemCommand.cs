using MediatR;

namespace Tinisoft.Application.Inventory.Commands.PickOrderItem;

public class PickOrderItemCommand : IRequest<PickOrderItemResponse>
{
    public Guid OrderItemId { get; set; }
    public Guid WarehouseLocationId { get; set; } // Hangi lokasyondan alındı
    public int Quantity { get; set; } // Kaç adet alındı
    public Guid? PickedByUserId { get; set; } // Kim topladı
}

public class PickOrderItemResponse
{
    public Guid OrderItemId { get; set; }
    public bool Success { get; set; }
    public string? Message { get; set; }
}



