namespace Tinisoft.Application.Shipping.Services;

/// <summary>
/// Kargo firması entegrasyon servisi interface'i
/// </summary>
public interface IShippingService
{
    /// <summary>
    /// Kargo fiyatını hesapla
    /// </summary>
    Task<decimal?> CalculateShippingCostAsync(
        string providerCode,
        string fromCity,
        string toCity,
        decimal weight,
        decimal? width = null,
        decimal? height = null,
        decimal? depth = null,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Kargo takip numarası oluştur (gönderi oluştur)
    /// </summary>
    Task<CreateShipmentResponse> CreateShipmentAsync(
        string providerCode,
        CreateShipmentRequest request,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Kargo takip bilgilerini sorgula
    /// </summary>
    Task<TrackingResponse> TrackShipmentAsync(
        string providerCode,
        string trackingNumber,
        CancellationToken cancellationToken = default);
}

public class CreateShipmentRequest
{
    public string RecipientName { get; set; } = string.Empty;
    public string RecipientPhone { get; set; } = string.Empty;
    public string AddressLine1 { get; set; } = string.Empty;
    public string? AddressLine2 { get; set; }
    public string City { get; set; } = string.Empty;
    public string State { get; set; } = string.Empty;
    public string PostalCode { get; set; } = string.Empty;
    public string Country { get; set; } = string.Empty;
    public decimal Weight { get; set; }
    public decimal? Width { get; set; }
    public decimal? Height { get; set; }
    public decimal? Depth { get; set; }
    public int PackageCount { get; set; } = 1;
    public string? OrderNumber { get; set; }
}

public class CreateShipmentResponse
{
    public string TrackingNumber { get; set; } = string.Empty;
    public string? LabelUrl { get; set; }
    public decimal ShippingCost { get; set; }
    public string? ProviderResponseJson { get; set; }
    public bool Success { get; set; }
    public string? ErrorMessage { get; set; }
}

public class TrackingResponse
{
    public string TrackingNumber { get; set; } = string.Empty;
    public string Status { get; set; } = string.Empty; // "InTransit", "Delivered", "Returned", vb.
    public List<TrackingEvent> Events { get; set; } = new();
    public DateTime? EstimatedDeliveryDate { get; set; }
    public bool Success { get; set; }
    public string? ErrorMessage { get; set; }
}

public class TrackingEvent
{
    public DateTime Date { get; set; }
    public string Location { get; set; } = string.Empty;
    public string Description { get; set; } = string.Empty;
    public string Status { get; set; } = string.Empty;
}

