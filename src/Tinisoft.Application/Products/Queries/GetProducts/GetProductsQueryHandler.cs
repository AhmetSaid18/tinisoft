using MediatR;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Caching.Distributed;
using System.Text.Json;
using Tinisoft.Infrastructure.Persistence;
using Finbuckle.MultiTenant;

namespace Tinisoft.Application.Products.Queries.GetProducts;

public class GetProductsQueryHandler : IRequestHandler<GetProductsQuery, GetProductsResponse>
{
    private readonly ApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly IDistributedCache _cache;
    private readonly ILogger<GetProductsQueryHandler> _logger;

    public GetProductsQueryHandler(
        ApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor,
        IDistributedCache cache,
        ILogger<GetProductsQueryHandler> logger)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
        _cache = cache;
        _logger = logger;
    }

    public async Task<GetProductsResponse> Handle(GetProductsQuery request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        // Cache key
        var cacheKey = $"products:list:{tenantId}:{request.Page}:{request.PageSize}:{request.Search}:{request.CategoryId}:{request.IsActive}:{request.SortBy}:{request.SortOrder}";
        
        // Try cache first
        var cachedResult = await _cache.GetStringAsync(cacheKey, cancellationToken);
        if (!string.IsNullOrEmpty(cachedResult))
        {
            return JsonSerializer.Deserialize<GetProductsResponse>(cachedResult)!;
        }

        var query = _dbContext.Products
            .Where(p => p.TenantId == tenantId)
            .AsQueryable();

        // Filters
        if (!string.IsNullOrEmpty(request.Search))
        {
            query = query.Where(p => 
                p.Title.Contains(request.Search) || 
                (p.SKU != null && p.SKU.Contains(request.Search)) ||
                (p.Description != null && p.Description.Contains(request.Search)));
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

        var totalCount = await query.CountAsync(cancellationToken);

        var products = await query
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
            .Skip((request.Page - 1) * request.PageSize)
            .Take(request.PageSize)
            .ToListAsync(cancellationToken);

        var response = new GetProductsResponse
        {
            Items = products,
            TotalCount = totalCount,
            Page = request.Page,
            PageSize = request.PageSize
        };

        // Cache for 5 minutes
        var cacheOptions = new DistributedCacheEntryOptions
        {
            AbsoluteExpirationRelativeToNow = TimeSpan.FromMinutes(5)
        };
        await _cache.SetStringAsync(cacheKey, JsonSerializer.Serialize(response), cacheOptions, cancellationToken);

        return response;
    }
}
