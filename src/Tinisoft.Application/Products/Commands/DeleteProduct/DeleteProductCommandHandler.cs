using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Infrastructure.Persistence;
using Tinisoft.Shared.Events;
using Tinisoft.Shared.Contracts;
using Finbuckle.MultiTenant;

namespace Tinisoft.Application.Products.Commands.DeleteProduct;

public class DeleteProductCommandHandler : IRequestHandler<DeleteProductCommand, Unit>
{
    private readonly ApplicationDbContext _dbContext;
    private readonly IEventBus _eventBus;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly ILogger<DeleteProductCommandHandler> _logger;

    public DeleteProductCommandHandler(
        ApplicationDbContext dbContext,
        IEventBus eventBus,
        IMultiTenantContextAccessor tenantAccessor,
        ILogger<DeleteProductCommandHandler> logger)
    {
        _dbContext = dbContext;
        _eventBus = eventBus;
        _tenantAccessor = tenantAccessor;
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

        _dbContext.Products.Remove(product);
        await _dbContext.SaveChangesAsync(cancellationToken);

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

