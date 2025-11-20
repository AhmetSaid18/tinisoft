using Tinisoft.Domain.Entities;

namespace Tinisoft.Application.Marketplace.Services;

public class HepsiburadaMarketplaceService : IMarketplaceService
{
    private readonly ILogger<HepsiburadaMarketplaceService> _logger;

    public HepsiburadaMarketplaceService(ILogger<HepsiburadaMarketplaceService> logger)
    {
        _logger = logger;
    }

    public async Task<SyncProductsResponse> SyncProductsAsync(MarketplaceIntegration integration, List<Guid>? productIds, CancellationToken cancellationToken)
    {
        _logger.LogInformation("Syncing products to Hepsiburada for integration {IntegrationId}", integration.Id);
        
        await Task.Delay(100, cancellationToken);
        
        return new SyncProductsResponse
        {
            SyncedCount = productIds?.Count ?? 10,
            FailedCount = 0,
            Errors = new List<string>()
        };
    }

    public async Task<SyncOrdersResponse> SyncOrdersAsync(MarketplaceIntegration integration, CancellationToken cancellationToken)
    {
        _logger.LogInformation("Syncing orders from Hepsiburada for integration {IntegrationId}", integration.Id);
        
        await Task.Delay(100, cancellationToken);
        
        return new SyncOrdersResponse
        {
            SyncedCount = 5,
            FailedCount = 0,
            Errors = new List<string>()
        };
    }
}



