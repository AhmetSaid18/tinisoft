using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Application.Common.Interfaces;
using Tinisoft.Shared.Contracts;
using Tinisoft.Application.Products.Services;
using Tinisoft.Shared.Events;
using Tinisoft.Shared.Contracts;
using Finbuckle.MultiTenant;

namespace Tinisoft.Application.Products.Commands.DeleteProduct;

public class DeleteProductCommandHandler : IRequestHandler<DeleteProductCommand, Unit>
{
    private readonly IApplicationDbContext _dbContext;
    private readonly IEventBus _eventBus;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly IMeilisearchService _meilisearchService;
    private readonly ILogger<DeleteProductCommandHandler> _logger;

    public DeleteProductCommandHandler(
        IApplicationDbContext dbContext,
        IEventBus eventBus,
        IMultiTenantContextAccessor tenantAccessor,
        IMeilisearchService meilisearchService,
        ILogger<DeleteProductCommandHandler> logger)
    {
        _dbContext = dbContext;
        _eventBus = eventBus;
        _tenantAccessor = tenantAccessor;
        _meilisearchService = meilisearchService;
        _logger = logger;
    }

    public async Task<Unit> Handle(DeleteProductCommand request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        var product = await _dbContext.Products
            .FirstOrDefaultAsync(p => p.Id == request.ProductId && p.TenantId == tenantId, cancellationToken);

        if (product == null)
        {
            throw new KeyNotFoundException($"Ürün bulunamadı: {request.ProductId}");
        }

        var productId = product.Id;
        _dbContext.Products.Remove(product);
        await _dbContext.SaveChangesAsync(cancellationToken);

        // Meilisearch delete (background)
        _ = Task.Run(async () =>
        {
            try
            {
                await _meilisearchService.DeleteProductAsync(productId, tenantId, cancellationToken);
            }
            catch (Exception ex)
            {
                _logger.LogWarning(ex, "Meilisearch delete failed for product: {ProductId}", productId);
            }
        }, cancellationToken);

        // Event publish
        await _eventBus.PublishAsync(new ProductDeletedEvent
        {
            ProductId = product.Id,
            TenantId = tenantId
        }, cancellationToken);

        _logger.LogInformation("Product deleted: {ProductId}", product.Id);

        return Unit.Value;
    }
}



