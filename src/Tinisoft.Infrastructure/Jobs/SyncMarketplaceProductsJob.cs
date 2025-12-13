using Hangfire;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;
using Tinisoft.Application.Marketplace.Services;
using Tinisoft.Infrastructure.Persistence;

namespace Tinisoft.Infrastructure.Jobs;

/// <summary>
/// Marketplace'lere ürün senkronizasyonu yapan Hangfire job
/// </summary>
public class SyncMarketplaceProductsJob
{
    private readonly ApplicationDbContext _dbContext;
    private readonly IMarketplaceServiceFactory _marketplaceServiceFactory;
    private readonly ILogger<SyncMarketplaceProductsJob> _logger;

    public SyncMarketplaceProductsJob(
        ApplicationDbContext dbContext,
        IMarketplaceServiceFactory marketplaceServiceFactory,
        ILogger<SyncMarketplaceProductsJob> logger)
    {
        _dbContext = dbContext;
        _marketplaceServiceFactory = marketplaceServiceFactory;
        _logger = logger;
    }

    /// <summary>
    /// Tüm aktif marketplace entegrasyonları için ürün senkronizasyonu yapar
    /// </summary>
    [AutomaticRetry(Attempts = 3, DelaysInSeconds = new[] { 300, 900, 1800 })]
    public async Task ExecuteAsync(CancellationToken cancellationToken = default)
    {
        try
        {
            _logger.LogInformation("Starting marketplace product sync job");

            // Aktif marketplace entegrasyonlarını al (AutoSyncProducts = true olanlar)
            var activeIntegrations = await _dbContext.MarketplaceIntegrations
                .Where(mi => mi.IsActive && mi.AutoSyncProducts)
                .ToListAsync(cancellationToken);

            if (activeIntegrations.Count == 0)
            {
                _logger.LogInformation("No active marketplace integrations found for product sync");
                return;
            }

            var totalSynced = 0;
            var totalFailed = 0;

            foreach (var integration in activeIntegrations)
            {
                try
                {
                    _logger.LogInformation("Syncing products for {Marketplace} (Tenant: {TenantId})", 
                        integration.Marketplace, integration.TenantId);

                    var service = _marketplaceServiceFactory.GetService(integration.Marketplace);
                    var result = await service.SyncProductsAsync(integration, null, cancellationToken);

                    totalSynced += result.SyncedCount;
                    totalFailed += result.FailedCount;

                    // Update last sync info
                    integration.LastSyncAt = DateTime.UtcNow;
                    integration.LastSyncStatus = result.FailedCount > 0 
                        ? $"Partial: {result.SyncedCount} synced, {result.FailedCount} failed"
                        : $"Success: {result.SyncedCount} products synced";

                    if (result.Errors.Count > 0)
                    {
                        _logger.LogWarning("Sync errors for {Marketplace}: {Errors}", 
                            integration.Marketplace, string.Join(", ", result.Errors));
                    }
                }
                catch (Exception ex)
                {
                    _logger.LogError(ex, "Error syncing products for {Marketplace} (Tenant: {TenantId})", 
                        integration.Marketplace, integration.TenantId);
                    
                    integration.LastSyncAt = DateTime.UtcNow;
                    integration.LastSyncStatus = $"Failed: {ex.Message}";
                }
            }

            await _dbContext.SaveChangesAsync(cancellationToken);

            _logger.LogInformation(
                "Marketplace product sync completed. Total synced: {Synced}, Total failed: {Failed}",
                totalSynced, totalFailed);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error in marketplace product sync job");
            throw; // Hangfire retry için
        }
    }

    /// <summary>
    /// Belirli bir tenant için ürün senkronizasyonu yapar
    /// </summary>
    [AutomaticRetry(Attempts = 2, DelaysInSeconds = new[] { 60, 300 })]
    public async Task ExecuteForTenantAsync(Guid tenantId, CancellationToken cancellationToken = default)
    {
        try
        {
            _logger.LogInformation("Starting marketplace product sync for tenant {TenantId}", tenantId);

            var activeIntegrations = await _dbContext.MarketplaceIntegrations
                .Where(mi => mi.TenantId == tenantId && mi.IsActive && mi.AutoSyncProducts)
                .ToListAsync(cancellationToken);

            if (activeIntegrations.Count == 0)
            {
                _logger.LogInformation("No active marketplace integrations found for tenant {TenantId}", tenantId);
                return;
            }

            foreach (var integration in activeIntegrations)
            {
                try
                {
                    var service = _marketplaceServiceFactory.GetService(integration.Marketplace);
                    var result = await service.SyncProductsAsync(integration, null, cancellationToken);

                    integration.LastSyncAt = DateTime.UtcNow;
                    integration.LastSyncStatus = result.FailedCount > 0 
                        ? $"Partial: {result.SyncedCount} synced, {result.FailedCount} failed"
                        : $"Success: {result.SyncedCount} products synced";

                    _logger.LogInformation("Synced {Count} products to {Marketplace} for tenant {TenantId}",
                        result.SyncedCount, integration.Marketplace, tenantId);
                }
                catch (Exception ex)
                {
                    _logger.LogError(ex, "Error syncing products for {Marketplace} (Tenant: {TenantId})", 
                        integration.Marketplace, tenantId);
                }
            }

            await _dbContext.SaveChangesAsync(cancellationToken);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error in marketplace product sync for tenant {TenantId}", tenantId);
            throw;
        }
    }
}

