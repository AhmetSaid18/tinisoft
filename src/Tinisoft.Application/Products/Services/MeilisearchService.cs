using Meilisearch;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;
using Tinisoft.Domain.Entities;
using Tinisoft.Infrastructure.Persistence;

namespace Tinisoft.Application.Products.Services;

public class MeilisearchService : IMeilisearchService
{
    private readonly MeilisearchClient? _meilisearchClient;
    private readonly ApplicationDbContext _dbContext;
    private readonly ILogger<MeilisearchService> _logger;

    public MeilisearchService(
        MeilisearchClient? meilisearchClient,
        ApplicationDbContext dbContext,
        ILogger<MeilisearchService> logger)
    {
        _meilisearchClient = meilisearchClient;
        _dbContext = dbContext;
        _logger = logger;
    }

    public async Task IndexProductAsync(Product product, CancellationToken cancellationToken = default)
    {
        if (_meilisearchClient == null)
        {
            _logger.LogWarning("Meilisearch client is not configured");
            return;
        }

        try
        {
            var index = _meilisearchClient.Index($"products_{product.TenantId}");
            
            // Index oluştur (yoksa)
            try
            {
                await index.GetAsync(cancellationToken);
            }
            catch
            {
                await _meilisearchClient.CreateIndexAsync($"products_{product.TenantId}", "id", cancellationToken);
                
                // Searchable attributes
                var settings = new Settings
                {
                    SearchableAttributes = new[] { "title", "description", "sku" },
                    FilterableAttributes = new[] { "categoryId", "isActive", "price" },
                    SortableAttributes = new[] { "price", "createdAt", "title" }
                };
                await index.UpdateSettingsAsync(settings, cancellationToken);
            }

            // ProductCategories'i yükle (eğer yüklenmemişse)
            if (product.ProductCategories == null || !product.ProductCategories.Any())
            {
                await _dbContext.Entry(product)
                    .Collection(p => p.ProductCategories)
                    .LoadAsync(cancellationToken);
            }

            var document = new
            {
                id = product.Id.ToString(),
                title = product.Title,
                description = product.Description,
                sku = product.SKU,
                price = product.Price,
                isActive = product.IsActive,
                categoryId = product.ProductCategories?.Select(pc => pc.CategoryId.ToString()).FirstOrDefault(),
                createdAt = product.CreatedAt
            };

            await index.AddDocumentsAsync(new[] { document }, cancellationToken: cancellationToken);
            _logger.LogInformation("Product indexed: {ProductId}", product.Id);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error indexing product: {ProductId}", product.Id);
            // Meilisearch hatası kritik değil, devam et
        }
    }

    public async Task UpdateProductAsync(Product product, CancellationToken cancellationToken = default)
    {
        await IndexProductAsync(product, cancellationToken);
    }

    public async Task DeleteProductAsync(Guid productId, Guid tenantId, CancellationToken cancellationToken = default)
    {
        if (_meilisearchClient == null)
        {
            return;
        }

        try
        {
            var index = _meilisearchClient.Index($"products_{tenantId}");
            await index.DeleteOneDocumentAsync(productId.ToString(), cancellationToken);
            _logger.LogInformation("Product deleted from index: {ProductId}", productId);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error deleting product from index: {ProductId}", productId);
        }
    }

    public async Task ReindexAllProductsAsync(Guid tenantId, CancellationToken cancellationToken = default)
    {
        if (_meilisearchClient == null)
        {
            return;
        }

        try
        {
            var products = await _dbContext.Products
                .AsNoTracking()
                .Include(p => p.ProductCategories)
                .Where(p => p.TenantId == tenantId)
                .ToListAsync(cancellationToken);

            var documents = products.Select(p => new
            {
                id = p.Id.ToString(),
                title = p.Title,
                description = p.Description,
                sku = p.SKU,
                price = p.Price,
                isActive = p.IsActive,
                categoryId = p.ProductCategories.Select(pc => pc.CategoryId.ToString()).FirstOrDefault(),
                createdAt = p.CreatedAt
            }).ToList();

            var index = _meilisearchClient.Index($"products_{tenantId}");
            
            // Index oluştur
            try
            {
                await index.GetAsync(cancellationToken);
            }
            catch
            {
                await _meilisearchClient.CreateIndexAsync($"products_{tenantId}", "id", cancellationToken);
            }

            // Tüm dokümanları ekle
            await index.AddDocumentsAsync(documents, cancellationToken: cancellationToken);
            
            _logger.LogInformation("Reindexed {Count} products for tenant: {TenantId}", documents.Count, tenantId);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error reindexing products for tenant: {TenantId}", tenantId);
        }
    }
}

