using Tinisoft.Domain.Entities;

namespace Tinisoft.Application.Marketplace.Services;

public interface IMarketplaceService
{
    Task<SyncProductsResponse> SyncProductsAsync(MarketplaceIntegration integration, List<Guid>? productIds, CancellationToken cancellationToken);
    Task<SyncOrdersResponse> SyncOrdersAsync(MarketplaceIntegration integration, CancellationToken cancellationToken);
}

public class SyncProductsResponse
{
    public int SyncedCount { get; set; }
    public int FailedCount { get; set; }
    public List<string> Errors { get; set; } = new();
}

public class SyncOrdersResponse
{
    public int SyncedCount { get; set; }
    public int FailedCount { get; set; }
    public List<string> Errors { get; set; } = new();
}

