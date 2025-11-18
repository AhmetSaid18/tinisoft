using Tinisoft.Application.Shipping.Services;
using Microsoft.Extensions.Logging;

namespace Tinisoft.Infrastructure.Services;

/// <summary>
/// MNG Kargo entegrasyonu
/// </summary>
public class MngShippingService : IShippingService
{
    private readonly ILogger<MngShippingService> _logger;

    public MngShippingService(ILogger<MngShippingService> logger)
    {
        _logger = logger;
    }

    public async Task<decimal?> CalculateShippingCostAsync(
        string providerCode,
        string fromCity,
        string toCity,
        decimal weight,
        decimal? width = null,
        decimal? height = null,
        decimal? depth = null,
        CancellationToken cancellationToken = default)
    {
        // TODO: MNG Kargo API entegrasyonu
        _logger.LogInformation("Calculating shipping cost for MNG Kargo: {FromCity} -> {ToCity}, Weight: {Weight}kg", 
            fromCity, toCity, weight);
        
        var baseCost = 20.00m;
        var weightCost = weight * 2.0m;
        
        return baseCost + weightCost;
    }

    public async Task<CreateShipmentResponse> CreateShipmentAsync(
        string providerCode,
        CreateShipmentRequest request,
        CancellationToken cancellationToken = default)
    {
        // TODO: MNG Kargo API entegrasyonu
        _logger.LogInformation("Creating shipment for MNG Kargo: {RecipientName}, {City}", 
            request.RecipientName, request.City);

        var trackingNumber = $"MNG{DateTime.UtcNow:yyyyMMdd}{Guid.NewGuid().ToString("N").Substring(0, 8).ToUpper()}";
        
        return new CreateShipmentResponse
        {
            TrackingNumber = trackingNumber,
            LabelUrl = null,
            ShippingCost = await CalculateShippingCostAsync(providerCode, "Istanbul", request.City, request.Weight, 
                request.Width, request.Height, request.Depth, cancellationToken) ?? 0,
            Success = true
        };
    }

    public async Task<TrackingResponse> TrackShipmentAsync(
        string providerCode,
        string trackingNumber,
        CancellationToken cancellationToken = default)
    {
        // TODO: MNG Kargo takip API entegrasyonu
        _logger.LogInformation("Tracking shipment for MNG Kargo: {TrackingNumber}", trackingNumber);

        return new TrackingResponse
        {
            TrackingNumber = trackingNumber,
            Status = "InTransit",
            Events = new List<TrackingEvent>
            {
                new TrackingEvent
                {
                    Date = DateTime.UtcNow.AddDays(-1),
                    Location = "Istanbul",
                    Description = "Gönderi alındı",
                    Status = "Received"
                }
            },
            Success = true
        };
    }
}

