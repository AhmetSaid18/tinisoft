using Tinisoft.Domain.Entities;

namespace Tinisoft.Application.Marketplace.Services;

public class N11MarketplaceService : IMarketplaceService
{
    private readonly ILogger<N11MarketplaceService> _logger;

    public N11MarketplaceService(ILogger<N11MarketplaceService> logger)
    {
        _logger = logger;
    }

    public async Task<SyncProductsResponse> SyncProductsAsync(MarketplaceIntegration integration, List<Guid>? productIds, CancellationToken cancellationToken)
    {
        _logger.LogInformation("Syncing products to N11 for integration {IntegrationId}", integration.Id);
        
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
        _logger.LogInformation("Syncing orders from N11 for integration {IntegrationId}", integration.Id);
        
        await Task.Delay(100, cancellationToken);
        
        return new SyncOrdersResponse
        {
            SyncedCount = 5,
            FailedCount = 0,
            Errors = new List<string>()
        };
    }
}



