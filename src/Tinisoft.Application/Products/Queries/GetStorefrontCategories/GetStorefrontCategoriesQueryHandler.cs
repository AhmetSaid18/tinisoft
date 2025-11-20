using MediatR;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Caching.Distributed;
using System.Text.Json;
using Tinisoft.Application.Common.Interfaces;
using Tinisoft.Shared.Contracts;
using Finbuckle.MultiTenant;

namespace Tinisoft.Application.Products.Queries.GetStorefrontCategories;

public class GetStorefrontCategoriesQueryHandler : IRequestHandler<GetStorefrontCategoriesQuery, GetStorefrontCategoriesResponse>
{
    private readonly IApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly IDistributedCache _cache;
    private readonly ILogger<GetStorefrontCategoriesQueryHandler> _logger;

    public GetStorefrontCategoriesQueryHandler(
        IApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor,
        IDistributedCache cache,
        ILogger<GetStorefrontCategoriesQueryHandler> logger)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
        _cache = cache;
        _logger = logger;
    }

    public async Task<GetStorefrontCategoriesResponse> Handle(GetStorefrontCategoriesQuery request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        // Cache key
        var cacheKey = $"storefront:categories:{tenantId}";

        // Cache kontrolü
        var cachedResult = await _cache.GetStringAsync(cacheKey, cancellationToken);
        if (!string.IsNullOrEmpty(cachedResult))
        {
            return JsonSerializer.Deserialize<GetStorefrontCategoriesResponse>(cachedResult)!;
        }

        // Sadece aktif kategorileri getir
        var categories = await _dbContext.Categories
            .AsNoTracking()
            .Where(c => c.TenantId == tenantId && c.IsActive)
            .OrderBy(c => c.DisplayOrder)
            .ThenBy(c => c.Name)
            .ToListAsync(cancellationToken);

        // Parent-child ilişkisini kur
        var categoryDict = new Dictionary<Guid, StorefrontCategoryDto>();
        var rootCategories = new List<StorefrontCategoryDto>();

        // Önce tüm kategorileri DTO'ya çevir
        foreach (var category in categories)
        {
            var dto = new StorefrontCategoryDto
            {
                Id = category.Id,
                Name = category.Name,
                Slug = category.Slug,
                Description = category.Description,
                ImageUrl = category.ImageUrl,
                ParentCategoryId = category.ParentCategoryId,
                DisplayOrder = category.DisplayOrder,
                SubCategories = new List<StorefrontCategoryDto>()
            };
            categoryDict[category.Id] = dto;
        }

        // Parent-child ilişkisini kur
        foreach (var category in categories)
        {
            var dto = categoryDict[category.Id];
            
            if (category.ParentCategoryId == null)
            {
                rootCategories.Add(dto);
            }
            else
            {
                // Parent'ı bul ve subcategory olarak ekle
                if (categoryDict.TryGetValue(category.ParentCategoryId.Value, out var parentDto))
                {
                    parentDto.SubCategories.Add(dto);
                }
            }
        }

        var response = new GetStorefrontCategoriesResponse
        {
            Categories = rootCategories
        };

        // Cache'e kaydet (30 dakika - kategoriler sık değişmez)
        await _cache.SetStringAsync(
            cacheKey,
            JsonSerializer.Serialize(response),
            new DistributedCacheEntryOptions { AbsoluteExpirationRelativeToNow = TimeSpan.FromMinutes(30) },
            cancellationToken);

        return response;
    }
}



