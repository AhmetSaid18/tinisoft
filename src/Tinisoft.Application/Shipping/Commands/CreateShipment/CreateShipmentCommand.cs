using MediatR;

namespace Tinisoft.Application.Shipping.Commands.CreateShipment;

public class CreateShipmentCommand : IRequest<CreateShipmentResponse>
{
    public Guid OrderId { get; set; }
    public Guid ShippingProviderId { get; set; }
    
    // Gönderi bilgileri
    public string RecipientName { get; set; } = string.Empty;
    public string RecipientPhone { get; set; } = string.Empty;
    public string AddressLine1 { get; set; } = string.Empty;
    public string? AddressLine2 { get; set; }
    public string City { get; set; } = string.Empty;
    public string State { get; set; } = string.Empty;
    public string PostalCode { get; set; } = string.Empty;
    public string Country { get; set; } = string.Empty;
    
    // Paket bilgileri
    public decimal Weight { get; set; }
    public decimal? Width { get; set; }
    public decimal? Height { get; set; }
    public decimal? Depth { get; set; }
    public int PackageCount { get; set; } = 1;
}

public class CreateShipmentResponse
{
    public Guid ShipmentId { get; set; }
    public string TrackingNumber { get; set; } = string.Empty;
    public string? LabelUrl { get; set; }
    public decimal ShippingCost { get; set; }
    public bool Success { get; set; }
    public string? ErrorMessage { get; set; }
}



