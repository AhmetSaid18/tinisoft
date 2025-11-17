using MediatR;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Caching.Distributed;
using System.Text;
using System.Text.Json;
using Tinisoft.Infrastructure.Persistence;
using Tinisoft.Infrastructure.Services;
using Finbuckle.MultiTenant;
using Meilisearch;

namespace Tinisoft.Application.Products.Queries.GetProductsCursor;

/// <summary>
/// Cursor-based pagination handler - Shopify tarzı performanslı pagination
/// Milyarlarca ürün için optimize edilmiştir
/// </summary>
public class GetProductsCursorQueryHandler : IRequestHandler<GetProductsCursorQuery, GetProductsCursorResponse>
{
    private readonly ApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly IDistributedCache _cache;
    private readonly MeilisearchClient? _meilisearchClient;
    private readonly CircuitBreakerService _circuitBreaker;
    private readonly ILogger<GetProductsCursorQueryHandler> _logger;

    public GetProductsCursorQueryHandler(
        ApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor,
        IDistributedCache cache,
        MeilisearchClient? meilisearchClient,
        CircuitBreakerService circuitBreaker,
        ILogger<GetProductsCursorQueryHandler> logger)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
        _cache = cache;
        _meilisearchClient = meilisearchClient;
        _circuitBreaker = circuitBreaker;
        _logger = logger;
    }

    public async Task<GetProductsCursorResponse> Handle(GetProductsCursorQuery request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);
        var validatedLimit = request.GetValidatedLimit();

        // Circuit Breaker kontrolü - Database yükü çok olduğunda koruma
        if (await _circuitBreaker.IsCircuitOpenAsync(cancellationToken))
        {
            _logger.LogWarning("Circuit breaker is OPEN - returning cached or default response");
            // Circuit açıkken cache'den döndür veya default response
            var cacheKey = $"products:cursor:{tenantId}:{validatedLimit}:{request.Cursor}:{request.Search}:{request.CategoryId}:{request.IsActive}:{request.SortBy}:{request.SortOrder}";
            var cachedResult = await _cache.GetStringAsync(cacheKey, cancellationToken);
            if (!string.IsNullOrEmpty(cachedResult))
            {
                return JsonSerializer.Deserialize<GetProductsCursorResponse>(cachedResult)!;
            }
            
            // Cache de yoksa boş response döndür (circuit açıkken database'e gitme)
            return new GetProductsCursorResponse
            {
                Items = new List<ProductListItemDto>(),
                HasNextPage = false,
                HasPreviousPage = false,
                Limit = validatedLimit
            };
        }

        // Cache key
        var cacheKey2 = $"products:cursor:{tenantId}:{validatedLimit}:{request.Cursor}:{request.Search}:{request.CategoryId}:{request.IsActive}:{request.SortBy}:{request.SortOrder}";
        
        // Try cache first
        var cachedResult2 = await _cache.GetStringAsync(cacheKey2, cancellationToken);
        if (!string.IsNullOrEmpty(cachedResult2))
        {
            await _circuitBreaker.RecordSuccessAsync(cancellationToken);
            return JsonSerializer.Deserialize<GetProductsCursorResponse>(cachedResult2)!;
        }

        // Eğer search varsa Meilisearch kullan, yoksa database'den cursor-based pagination
        if (!string.IsNullOrWhiteSpace(request.Search) && _meilisearchClient != null)
        {
            return await SearchWithMeilisearchAsync(tenantId, request, validatedLimit, cancellationToken);
        }

        // Database cursor-based pagination
        return await GetProductsWithCursorAsync(tenantId, request, validatedLimit, cacheKey, cancellationToken);
    }

    private async Task<GetProductsCursorResponse> GetProductsWithCursorAsync(
        Guid tenantId,
        GetProductsCursorQuery request,
        int limit,
        string cacheKey,
        CancellationToken cancellationToken)
    {
        var query = _dbContext.Products
            .Where(p => p.TenantId == tenantId)
            .AsNoTracking()
            .AsQueryable();

        // Cursor decode ve filtreleme
        Guid? cursorId = null;
        DateTime? cursorDate = null;
        decimal? cursorPrice = null;
        
        if (!string.IsNullOrWhiteSpace(request.Cursor))
        {
            try
            {
                var cursorBytes = Convert.FromBase64String(request.Cursor);
                var cursorString = Encoding.UTF8.GetString(cursorBytes);
                
                // Cursor format: "id:guid", "date:datetime", veya "price:decimal|id:guid"
                if (cursorString.StartsWith("id:"))
                {
                    cursorId = Guid.Parse(cursorString.Substring(3));
                }
                else if (cursorString.StartsWith("date:"))
                {
                    cursorDate = DateTime.Parse(cursorString.Substring(5));
                }
                else if (cursorString.StartsWith("price:"))
                {
                    var parts = cursorString.Substring(6).Split('|');
                    if (parts.Length >= 1)
                    {
                        cursorPrice = decimal.Parse(parts[0]);
                    }
                    if (parts.Length >= 2 && parts[1].StartsWith("id:"))
                    {
                        cursorId = Guid.Parse(parts[1].Substring(3));
                    }
                }
            }
            catch
            {
                // Invalid cursor, ignore
            }
        }

        // Filters
        if (request.CategoryId.HasValue)
        {
            query = query.Where(p => p.ProductCategories.Any(pc => pc.CategoryId == request.CategoryId.Value));
        }

        if (request.IsActive.HasValue)
        {
            query = query.Where(p => p.IsActive == request.IsActive.Value);
        }

        // Cursor-based filtering (Shopify tarzı)
        // SortBy'a göre cursor uygula
        var sortBy = request.SortBy?.ToLower() ?? "createdat";
        var sortOrder = request.SortOrder?.ToLower() ?? "desc";

        if (sortBy == "createdat")
        {
            if (cursorDate.HasValue)
            {
                query = sortOrder == "desc"
                    ? query.Where(p => p.CreatedAt < cursorDate.Value)
                    : query.Where(p => p.CreatedAt > cursorDate.Value);
            }

            query = sortOrder == "desc"
                ? query.OrderByDescending(p => p.CreatedAt).ThenByDescending(p => p.Id)
                : query.OrderBy(p => p.CreatedAt).ThenBy(p => p.Id);
        }
        else if (sortBy == "price")
        {
            // Price sorting için cursor
            if (cursorPrice.HasValue && cursorId.HasValue)
            {
                query = sortOrder == "desc"
                    ? query.Where(p => p.Price < cursorPrice.Value || 
                                      (p.Price == cursorPrice.Value && p.Id.CompareTo(cursorId.Value) < 0))
                    : query.Where(p => p.Price > cursorPrice.Value || 
                                      (p.Price == cursorPrice.Value && p.Id.CompareTo(cursorId.Value) > 0));
            }

            query = sortOrder == "desc"
                ? query.OrderByDescending(p => p.Price).ThenByDescending(p => p.Id)
                : query.OrderBy(p => p.Price).ThenBy(p => p.Id);
        }
        else // title veya default
        {
            if (cursorId.HasValue)
            {
                // Title sorting için cursor karmaşık, ID kullan
                query = sortOrder == "desc"
                    ? query.Where(p => p.Id.CompareTo(cursorId.Value) < 0)
                    : query.Where(p => p.Id.CompareTo(cursorId.Value) > 0);
            }

            query = sortOrder == "desc"
                ? query.OrderByDescending(p => p.Title).ThenByDescending(p => p.Id)
                : query.OrderBy(p => p.Title).ThenBy(p => p.Id);
        }

        // Limit + 1 al (hasNextPage kontrolü için)
        List<ProductListItemDto> products;
        try
        {
            products = await query
                .Select(p => new ProductListItemDto
                {
                    Id = p.Id,
                    Title = p.Title,
                    Slug = p.Slug,
                    SKU = p.SKU,
                    Price = p.Price,
                    CompareAtPrice = p.CompareAtPrice,
                    InventoryQuantity = p.InventoryQuantity,
                    IsActive = p.IsActive,
                    FeaturedImageUrl = p.Images.Where(img => img.IsFeatured).Select(img => img.ThumbnailUrl ?? img.SmallUrl ?? img.OriginalUrl).FirstOrDefault(),
                    CreatedAt = p.CreatedAt
                })
                .Take(limit + 1) // +1 for hasNextPage check
                .ToListAsync(cancellationToken);
        }
        catch (Exception ex)
        {
            // Database hatası - Circuit breaker'e kaydet
            await _circuitBreaker.RecordFailureAsync(cancellationToken);
            _logger.LogError(ex, "Database query failed for tenant: {TenantId}", tenantId);
            throw; // Exception'ı yukarı fırlat
        }

        var hasNextPage = products.Count > limit;
        if (hasNextPage)
        {
            products.RemoveAt(products.Count - 1); // Son elemanı çıkar
        }

        // Next cursor oluştur
        string? nextCursor = null;
        if (hasNextPage && products.Count > 0)
        {
            var lastProduct = products.Last();
            string cursorValue;
            
            if (sortBy == "createdat")
            {
                cursorValue = $"date:{lastProduct.CreatedAt:O}";
            }
            else if (sortBy == "price")
            {
                cursorValue = $"price:{lastProduct.Price}|id:{lastProduct.Id}";
            }
            else
            {
                cursorValue = $"id:{lastProduct.Id}";
            }
            
            nextCursor = Convert.ToBase64String(Encoding.UTF8.GetBytes(cursorValue));
        }

        var response = new GetProductsCursorResponse
        {
            Items = products,
            NextCursor = nextCursor,
            HasNextPage = hasNextPage,
            HasPreviousPage = !string.IsNullOrWhiteSpace(request.Cursor),
            Limit = limit
        };

        // Cache for 5 minutes
        var cacheOptions = new DistributedCacheEntryOptions
        {
            AbsoluteExpirationRelativeToNow = TimeSpan.FromMinutes(5),
            SlidingExpiration = TimeSpan.FromMinutes(2)
        };
        await _cache.SetStringAsync(cacheKey2, JsonSerializer.Serialize(response), cacheOptions, cancellationToken);

        // Circuit breaker success kaydet
        await _circuitBreaker.RecordSuccessAsync(cancellationToken);

        return response;
    }

    private async Task<GetProductsCursorResponse> SearchWithMeilisearchAsync(
        Guid tenantId,
        GetProductsCursorQuery request,
        int limit,
        CancellationToken cancellationToken)
    {
        if (_meilisearchClient == null)
        {
            throw new InvalidOperationException("Meilisearch client is not configured");
        }

        var index = _meilisearchClient.Index($"products_{tenantId}");
        
        // Meilisearch search - basit API kullan
        var searchResult = await index.SearchAsync<ProductSearchDocument>(
            request.Search,
            new SearchQuery
            {
                Limit = limit,
                Offset = 0,
                Filter = BuildMeilisearchFilter(request),
                Sort = !string.IsNullOrWhiteSpace(request.SortBy) 
                    ? new[] { $"{request.SortBy}:{request.SortOrder ?? "asc"}" }
                    : null
            });

        var productIds = searchResult.Hits.Select(h => Guid.Parse(h.Id)).ToList();

        // Database'den detayları çek (Meilisearch sadece ID'leri döndürür)
        var products = await _dbContext.Products
            .AsNoTracking()
            .Where(p => productIds.Contains(p.Id) && p.TenantId == tenantId)
            .Select(p => new ProductListItemDto
            {
                Id = p.Id,
                Title = p.Title,
                Slug = p.Slug,
                SKU = p.SKU,
                Price = p.Price,
                CompareAtPrice = p.CompareAtPrice,
                InventoryQuantity = p.InventoryQuantity,
                IsActive = p.IsActive,
                FeaturedImageUrl = p.Images.Where(img => img.IsFeatured).Select(img => img.ThumbnailUrl ?? img.SmallUrl ?? img.OriginalUrl).FirstOrDefault(),
                CreatedAt = p.CreatedAt
            })
            .ToListAsync(cancellationToken);

        // Meilisearch sıralamasına göre düzenle
        var orderedProducts = productIds
            .Select(id => products.FirstOrDefault(p => p.Id == id))
            .Where(p => p != null)
            .Cast<ProductListItemDto>()
            .ToList();

        return new GetProductsCursorResponse
        {
            Items = orderedProducts,
            NextCursor = searchResult.Hits.Count == limit ? Convert.ToBase64String(Encoding.UTF8.GetBytes($"offset:{limit}")) : null,
            HasNextPage = searchResult.Hits.Count == limit,
            HasPreviousPage = false, // Meilisearch search için previous page yok
            Limit = limit
        };
    }

    private string? BuildMeilisearchFilter(GetProductsCursorQuery request)
    {
        var filters = new List<string>();
        
        if (request.CategoryId.HasValue)
        {
            filters.Add($"categoryId = {request.CategoryId.Value}");
        }
        
        if (request.IsActive.HasValue)
        {
            filters.Add($"isActive = {request.IsActive.Value}");
        }
        
        return filters.Any() ? string.Join(" AND ", filters) : null;
    }
}

// Meilisearch için document model
public class ProductSearchDocument
{
    public string Id { get; set; } = string.Empty;
    public string Title { get; set; } = string.Empty;
    public string? Description { get; set; }
    public string? SKU { get; set; }
    public decimal Price { get; set; }
    public bool IsActive { get; set; }
    public Guid? CategoryId { get; set; }
    public DateTime CreatedAt { get; set; }
}

