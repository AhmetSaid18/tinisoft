using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Infrastructure.Persistence;
using Finbuckle.MultiTenant;
using Tinisoft.Application.Marketplace.Services;
using Tinisoft.Domain.Entities;

namespace Tinisoft.Application.Marketplace.Commands.SyncProducts;

public class SyncProductsCommandHandler : IRequestHandler<SyncProductsCommand, SyncProductsResponse>
{
    private readonly ApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly IMarketplaceServiceFactory _marketplaceServiceFactory;
    private readonly ILogger<SyncProductsCommandHandler> _logger;

    public SyncProductsCommandHandler(
        ApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor,
        IMarketplaceServiceFactory marketplaceServiceFactory,
        ILogger<SyncProductsCommandHandler> logger)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
        _marketplaceServiceFactory = marketplaceServiceFactory;
        _logger = logger;
    }

    public async Task<SyncProductsResponse> Handle(SyncProductsCommand request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        var integration = await _dbContext.Set<Domain.Entities.MarketplaceIntegration>()
            .FirstOrDefaultAsync(m => 
                m.TenantId == tenantId && 
                m.Marketplace == request.Marketplace && 
                m.IsActive, cancellationToken);

        if (integration == null)
        {
            throw new InvalidOperationException($"{request.Marketplace} entegrasyonu bulunamadı veya aktif değil");
        }

        var service = _marketplaceServiceFactory.GetService(request.Marketplace);
        var serviceResult = await service.SyncProductsAsync(integration, request.ProductIds, cancellationToken);

        integration.LastSyncAt = DateTime.UtcNow;
        integration.LastSyncStatus = serviceResult.FailedCount == 0 ? "Success" : "Partial";
        await _dbContext.SaveChangesAsync(cancellationToken);

        return new SyncProductsResponse
        {
            SyncedCount = serviceResult.SyncedCount,
            FailedCount = serviceResult.FailedCount,
            Errors = serviceResult.Errors
        };
    }
}

