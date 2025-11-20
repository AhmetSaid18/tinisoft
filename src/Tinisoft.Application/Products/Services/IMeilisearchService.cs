using Tinisoft.Domain.Entities;

namespace Tinisoft.Application.Products.Services;

public interface IMeilisearchService
{
    Task IndexProductAsync(Product product, CancellationToken cancellationToken = default);
    Task UpdateProductAsync(Product product, CancellationToken cancellationToken = default);
    Task DeleteProductAsync(Guid productId, Guid tenantId, CancellationToken cancellationToken = default);
    Task ReindexAllProductsAsync(Guid tenantId, CancellationToken cancellationToken = default);
}



