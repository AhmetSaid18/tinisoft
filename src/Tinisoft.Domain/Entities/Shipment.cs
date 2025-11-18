using Tinisoft.Domain.Common;

namespace Tinisoft.Domain.Entities;

/// <summary>
/// Gönderi (Shipment) - Siparişin kargo firmasına gönderilmesi
/// </summary>
public class Shipment : BaseEntity, ITenantEntity
{
    public Guid TenantId { get; set; }
    public Tenant? Tenant { get; set; }

    public Guid OrderId { get; set; }
    public Order? Order { get; set; }

    public Guid ShippingProviderId { get; set; }
    public ShippingProvider? ShippingProvider { get; set; }

    // Kargo bilgileri
    public string TrackingNumber { get; set; } = string.Empty; // Kargo takip numarası
    public string? LabelUrl { get; set; } // Kargo etiketi URL'i
    public string Status { get; set; } = "Pending"; // Pending, Created, InTransit, Delivered, Returned

    // Gönderi bilgileri
    public decimal Weight { get; set; } // kg
    public decimal? Width { get; set; } // cm
    public decimal? Height { get; set; } // cm
    public decimal? Depth { get; set; } // cm
    public int PackageCount { get; set; } = 1; // Paket sayısı

    // Fiyat bilgileri
    public decimal ShippingCost { get; set; } // Kargo ücreti
    public string Currency { get; set; } = "TRY";

    // Tarih bilgileri
    public DateTime? ShippedAt { get; set; } // Gönderim tarihi
    public DateTime? DeliveredAt { get; set; } // Teslimat tarihi
    public DateTime? EstimatedDeliveryDate { get; set; } // Tahmini teslimat tarihi

    // Adres bilgileri (kargo firmasına gönderilen)
    public string RecipientName { get; set; } = string.Empty;
    public string RecipientPhone { get; set; } = string.Empty;
    public string AddressLine1 { get; set; } = string.Empty;
    public string? AddressLine2 { get; set; }
    public string City { get; set; } = string.Empty;
    public string State { get; set; } = string.Empty;
    public string PostalCode { get; set; } = string.Empty;
    public string Country { get; set; } = string.Empty;

    // API yanıt bilgileri (kargo firmasından gelen)
    public string? ProviderResponseJson { get; set; } // Kargo firması API yanıtı
    public string? ErrorMessage { get; set; } // Hata mesajı (varsa)
}

