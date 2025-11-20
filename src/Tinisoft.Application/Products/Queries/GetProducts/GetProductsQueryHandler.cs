using MediatR;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Caching.Distributed;
using System.Text.Json;
using Tinisoft.Application.Common.Interfaces;
using Tinisoft.Shared.Contracts;
using Tinisoft.Shared.Contracts;
using Finbuckle.MultiTenant;

namespace Tinisoft.Application.Products.Queries.GetProducts;

public class GetProductsQueryHandler : IRequestHandler<GetProductsQuery, GetProductsResponse>
{
    private readonly IApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly IDistributedCache _cache;
    private readonly ICircuitBreakerService _circuitBreaker;
    private readonly ILogger<GetProductsQueryHandler> _logger;

    public GetProductsQueryHandler(
        IApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor,
        IDistributedCache cache,
        ICircuitBreakerService circuitBreaker,
        ILogger<GetProductsQueryHandler> logger)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
        _cache = cache;
        _circuitBreaker = circuitBreaker;
        _logger = logger;
    }

    public async Task<GetProductsResponse> Handle(GetProductsQuery request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        // Circuit Breaker kontrolü
        if (await _circuitBreaker.IsCircuitOpenAsync(cancellationToken))
        {
            _logger.LogWarning("Circuit breaker is OPEN - returning cached response");
            var cacheKey = $"products:list:{tenantId}:{request.Page}:{request.PageSize}:{request.Search}:{request.CategoryId}:{request.IsActive}:{request.SortBy}:{request.SortOrder}";
            var cachedResult = await _cache.GetStringAsync(cacheKey, cancellationToken);
            if (!string.IsNullOrEmpty(cachedResult))
            {
                return JsonSerializer.Deserialize<GetProductsResponse>(cachedResult)!;
            }
            
            // Cache de yoksa boş response
            return new GetProductsResponse
            {
                Items = new List<ProductListItemDto>(),
                TotalCount = 0,
                Page = request.Page,
                PageSize = request.PageSize
            };
        }

        // Cache key
        var cacheKey2 = $"products:list:{tenantId}:{request.Page}:{request.PageSize}:{request.Search}:{request.CategoryId}:{request.IsActive}:{request.SortBy}:{request.SortOrder}";
        
        // Try cache first
        var cachedResult2 = await _cache.GetStringAsync(cacheKey2, cancellationToken);
        if (!string.IsNullOrEmpty(cachedResult2))
        {
            await _circuitBreaker.RecordSuccessAsync(cancellationToken);
            return JsonSerializer.Deserialize<GetProductsResponse>(cachedResult2)!;
        }

        // AsNoTracking() - Read-only query için performans
        var query = _dbContext.Products
            .Where(p => p.TenantId == tenantId)
            .AsNoTracking()
            .AsQueryable();

        // Filters
        if (!string.IsNullOrEmpty(request.Search))
        {
            // PostgreSQL Full-Text Search için optimize edilmiş arama
            // Contains yerine daha performanslı arama
            var searchLower = request.Search.ToLower();
            query = query.Where(p => 
                p.Title.ToLower().Contains(searchLower) || 
                (p.SKU != null && p.SKU.ToLower().Contains(searchLower)) ||
                (p.Description != null && p.Description.ToLower().Contains(searchLower)));
        }

        if (request.CategoryId.HasValue)
        {
            query = query.Where(p => p.ProductCategories.Any(pc => pc.CategoryId == request.CategoryId.Value));
        }

        if (request.IsActive.HasValue)
        {
            query = query.Where(p => p.IsActive == request.IsActive.Value);
        }

        // Sorting
        query = request.SortBy?.ToLower() switch
        {
            "title" => request.SortOrder == "desc" 
                ? query.OrderByDescending(p => p.Title)
                : query.OrderBy(p => p.Title),
            "price" => request.SortOrder == "desc"
                ? query.OrderByDescending(p => p.Price)
                : query.OrderBy(p => p.Price),
            "createdat" => request.SortOrder == "desc"
                ? query.OrderByDescending(p => p.CreatedAt)
                : query.OrderBy(p => p.CreatedAt),
            _ => query.OrderByDescending(p => p.CreatedAt)
        };

        // Validated page size
        var validatedPageSize = request.GetValidatedPageSize();
        var validatedPage = request.Page < 1 ? 1 : request.Page;

        int totalCount;
        List<ProductListItemDto> products;
        
        try
        {
            totalCount = await query.CountAsync(cancellationToken);

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
                .Skip((validatedPage - 1) * validatedPageSize)
                .Take(validatedPageSize)
                .ToListAsync(cancellationToken);
        }
        catch (Exception ex)
        {
            // Database hatası - Circuit breaker'e kaydet
            await _circuitBreaker.RecordFailureAsync(cancellationToken);
            _logger.LogError(ex, "Database query failed for tenant: {TenantId}", tenantId);
            throw; // Exception'ı yukarı fırlat
        }

        var response = new GetProductsResponse
        {
            Items = products,
            TotalCount = totalCount,
            Page = validatedPage,
            PageSize = validatedPageSize
        };

        // Cache for 5 minutes (product list için)
        var cacheOptions = new DistributedCacheEntryOptions
        {
            AbsoluteExpirationRelativeToNow = TimeSpan.FromMinutes(5),
            SlidingExpiration = TimeSpan.FromMinutes(2) // Son erişimden 2 dakika sonra expire
        };
        await _cache.SetStringAsync(cacheKey2, JsonSerializer.Serialize(response), cacheOptions, cancellationToken);

        // Circuit breaker success kaydet
        await _circuitBreaker.RecordSuccessAsync(cancellationToken);

        return response;
    }
}


