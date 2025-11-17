using Tinisoft.Domain.Entities;

namespace Tinisoft.Application.Marketplace.Services;

public class TrendyolMarketplaceService : IMarketplaceService
{
    private readonly ILogger<TrendyolMarketplaceService> _logger;

    public TrendyolMarketplaceService(ILogger<TrendyolMarketplaceService> logger)
    {
        _logger = logger;
    }

    public async Task<SyncProductsResponse> SyncProductsAsync(MarketplaceIntegration integration, List<Guid>? productIds, CancellationToken cancellationToken)
    {
        _logger.LogInformation("Syncing products to Trendyol for integration {IntegrationId}", integration.Id);
        
        // Trendyol API entegrasyonu buraya gelecek
        // Şimdilik mock response
        
        await Task.Delay(100, cancellationToken); // Simulate API call
        
        return new SyncProductsResponse
        {
            SyncedCount = productIds?.Count ?? 10,
            FailedCount = 0,
            Errors = new List<string>()
        };
    }

    public async Task<SyncOrdersResponse> SyncOrdersAsync(MarketplaceIntegration integration, CancellationToken cancellationToken)
    {
        _logger.LogInformation("Syncing orders from Trendyol for integration {IntegrationId}", integration.Id);
        
        await Task.Delay(100, cancellationToken);
        
        return new SyncOrdersResponse
        {
            SyncedCount = 5,
            FailedCount = 0,
            Errors = new List<string>()
        };
    }
}

