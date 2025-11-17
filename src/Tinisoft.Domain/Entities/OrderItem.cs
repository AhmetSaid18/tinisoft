using Tinisoft.Domain.Common;

namespace Tinisoft.Domain.Entities;

public class OrderItem : BaseEntity
{
    public Guid OrderId { get; set; }
    public Order? Order { get; set; }
    
    public Guid ProductId { get; set; }
    public Product? Product { get; set; }
    
    public Guid? ProductVariantId { get; set; }
    public ProductVariant? ProductVariant { get; set; }
    
    public string Title { get; set; } = string.Empty;
    public string? SKU { get; set; }
    public int Quantity { get; set; }
    public decimal UnitPrice { get; set; }
    public decimal TotalPrice { get; set; }
    
    // Depo ve lokasyon bilgileri (sipariş hazırlanırken doldurulur)
    public Guid? WarehouseId { get; set; }
    public Warehouse? Warehouse { get; set; }
    
    public Guid? WarehouseLocationId { get; set; }
    public WarehouseLocation? WarehouseLocation { get; set; }
    
    // Picking durumu
    public bool IsPicked { get; set; } = false; // Toplandı mı?
    public DateTime? PickedAt { get; set; } // Ne zaman toplandı?
    public Guid? PickedByUserId { get; set; } // Kim topladı?
    public User? PickedByUser { get; set; }
}

