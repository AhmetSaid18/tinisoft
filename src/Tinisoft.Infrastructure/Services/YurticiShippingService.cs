using Tinisoft.Application.Shipping.Services;
using Microsoft.Extensions.Logging;

namespace Tinisoft.Infrastructure.Services;

/// <summary>
/// Yurtiçi Kargo entegrasyonu
/// </summary>
public class YurticiShippingService : IShippingService
{
    private readonly ILogger<YurticiShippingService> _logger;

    public YurticiShippingService(ILogger<YurticiShippingService> logger)
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
        // TODO: Yurtiçi Kargo API entegrasyonu
        _logger.LogInformation("Calculating shipping cost for Yurtiçi Kargo: {FromCity} -> {ToCity}, Weight: {Weight}kg", 
            fromCity, toCity, weight);
        
        var baseCost = 22.00m;
        var weightCost = weight * 2.2m;
        
        return baseCost + weightCost;
    }

    public async Task<CreateShipmentResponse> CreateShipmentAsync(
        string providerCode,
        CreateShipmentRequest request,
        CancellationToken cancellationToken = default)
    {
        // TODO: Yurtiçi Kargo API entegrasyonu
        _logger.LogInformation("Creating shipment for Yurtiçi Kargo: {RecipientName}, {City}", 
            request.RecipientName, request.City);

        var trackingNumber = $"YURTICI{DateTime.UtcNow:yyyyMMdd}{Guid.NewGuid().ToString("N").Substring(0, 8).ToUpper()}";
        
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
        // TODO: Yurtiçi Kargo takip API entegrasyonu
        _logger.LogInformation("Tracking shipment for Yurtiçi Kargo: {TrackingNumber}", trackingNumber);

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

