using MediatR;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Caching.Distributed;
using System.Text.Json;
using Tinisoft.Application.Common.Interfaces;
using Tinisoft.Shared.Contracts;
using Tinisoft.Application.ExchangeRates.Services;
using Finbuckle.MultiTenant;

namespace Tinisoft.Application.Products.Queries.GetStorefrontProducts;

public class GetStorefrontProductsQueryHandler : IRequestHandler<GetStorefrontProductsQuery, GetStorefrontProductsResponse>
{
    private readonly IApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly IDistributedCache _cache;
    private readonly IExchangeRateService _exchangeRateService;
    private readonly ILogger<GetStorefrontProductsQueryHandler> _logger;

    public GetStorefrontProductsQueryHandler(
        IApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor,
        IDistributedCache cache,
        IExchangeRateService exchangeRateService,
        ILogger<GetStorefrontProductsQueryHandler> logger)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
        _cache = cache;
        _exchangeRateService = exchangeRateService;
        _logger = logger;
    }

    public async Task<GetStorefrontProductsResponse> Handle(GetStorefrontProductsQuery request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        // Tenant bilgilerini al (SaleCurrency için)
        var tenant = await _dbContext.Tenants
            .AsNoTracking()
            .FirstOrDefaultAsync(t => t.Id == tenantId, cancellationToken);

        if (tenant == null)
        {
            throw new KeyNotFoundException("Tenant bulunamadı");
        }

        // Display currency: müşterinin tercihi varsa onu kullan, yoksa tenant'ın SaleCurrency'sini kullan
        var displayCurrency = !string.IsNullOrEmpty(request.PreferredCurrency)
            ? request.PreferredCurrency.ToUpper()
            : (tenant.SaleCurrency ?? "TRY").ToUpper();

        // Cache key
        var cacheKey = $"storefront:products:{tenantId}:{request.Page}:{request.PageSize}:{request.Search}:{request.CategoryId}:{displayCurrency}:{request.SortBy}:{request.SortOrder}";

        // Cache kontrolü
        var cachedResult = await _cache.GetStringAsync(cacheKey, cancellationToken);
        if (!string.IsNullOrEmpty(cachedResult))
        {
            return JsonSerializer.Deserialize<GetStorefrontProductsResponse>(cachedResult)!;
        }

        // Sadece aktif ve published ürünleri getir
        var query = _dbContext.Products
            .AsNoTracking()
            .Where(p => p.TenantId == tenantId && p.IsActive && p.Status == "Active");

        // Search
        if (!string.IsNullOrEmpty(request.Search))
        {
            var searchLower = request.Search.ToLower();
            query = query.Where(p =>
                p.Title.ToLower().Contains(searchLower) ||
                (p.SKU != null && p.SKU.ToLower().Contains(searchLower)) ||
                (p.Description != null && p.Description.ToLower().Contains(searchLower)) ||
                (p.ShortDescription != null && p.ShortDescription.ToLower().Contains(searchLower)));
        }

        // Category filter
        if (request.CategoryId.HasValue)
        {
            query = query.Where(p => p.ProductCategories.Any(pc => pc.CategoryId == request.CategoryId.Value));
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

        var validatedPageSize = request.GetValidatedPageSize();
        var validatedPage = request.Page < 1 ? 1 : request.Page;

        int totalCount;
        List<Domain.Entities.Product> products;

        try
        {
            totalCount = await query.CountAsync(cancellationToken);
            products = await query
                .Include(p => p.Images.OrderBy(img => img.Position).Take(1)) // Sadece featured image
                .Include(p => p.ProductCategories)
                    .ThenInclude(pc => pc.Category)
                
                .Skip((validatedPage - 1) * validatedPageSize)
                .Take(validatedPageSize)
                .ToListAsync(cancellationToken);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Ürün listesi getirilirken hata oluştu");
            throw;
        }

        // Currency conversion için exchange rate al
        decimal? exchangeRate = null;
        var productCurrency = tenant.SaleCurrency ?? "TRY";
        if (productCurrency.ToUpper() != displayCurrency && displayCurrency != "TRY")
        {
            // TRY'den displayCurrency'e çevir
            if (displayCurrency == "TRY")
            {
                // Zaten TRY'de, çevirme gerekmez
            }
            else
            {
                // TRY -> displayCurrency için ters kur al (1 / rate)
                var rateToTry = await _exchangeRateService.GetRateAsync(displayCurrency, cancellationToken);
                if (rateToTry.HasValue && rateToTry.Value > 0)
                {
                    exchangeRate = 1 / rateToTry.Value;
                }
            }
        }
        else if (productCurrency.ToUpper() != displayCurrency && productCurrency != "TRY")
        {
            // productCurrency -> displayCurrency
            var rate = await _exchangeRateService.GetRateAsync(displayCurrency, cancellationToken);
            if (rate.HasValue)
            {
                exchangeRate = rate.Value;
            }
        }

        // DTO mapping + currency conversion
        var items = new List<StorefrontProductDto>();
        foreach (var product in products)
        {
            var price = product.Price;
            var compareAtPrice = product.CompareAtPrice;

            // Currency conversion
            if (exchangeRate.HasValue && product.Currency.ToUpper() != displayCurrency)
            {
                price = product.Price * exchangeRate.Value;
                if (compareAtPrice.HasValue)
                {
                    compareAtPrice = compareAtPrice.Value * exchangeRate.Value;
                }
            }

            items.Add(new StorefrontProductDto
            {
                Id = product.Id,
                Title = product.Title,
                Slug = product.Slug,
                ShortDescription = product.ShortDescription,
                SKU = product.SKU,
                Price = Math.Round(price, 2, MidpointRounding.AwayFromZero),
                CompareAtPrice = compareAtPrice.HasValue
                    ? Math.Round(compareAtPrice.Value, 2, MidpointRounding.AwayFromZero)
                    : null,
                Currency = displayCurrency,
                InventoryQuantity = product.InventoryQuantity,
                FeaturedImageUrl = product.Images.FirstOrDefault()?.OriginalUrl,
                Categories = product.ProductCategories.Select(pc => pc.Category?.Name ?? "").Where(n => !string.IsNullOrEmpty(n)).ToList(),
                CreatedAt = product.CreatedAt
            });
        }

        var response = new GetStorefrontProductsResponse
        {
            Items = items,
            TotalCount = totalCount,
            Page = validatedPage,
            PageSize = validatedPageSize,
            DisplayCurrency = displayCurrency
        };

        // Cache'e kaydet (5 dakika)
        await _cache.SetStringAsync(
            cacheKey,
            JsonSerializer.Serialize(response),
            new DistributedCacheEntryOptions { AbsoluteExpirationRelativeToNow = TimeSpan.FromMinutes(5) },
            cancellationToken);

        return response;
    }
}



