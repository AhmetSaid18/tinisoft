using MediatR;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Caching.Distributed;
using System.Text.Json;
using Tinisoft.Application.Common.Interfaces;
using Tinisoft.Shared.Contracts;
using Tinisoft.Application.ExchangeRates.Services;
using Finbuckle.MultiTenant;

namespace Tinisoft.Application.Products.Queries.GetStorefrontProduct;

public class GetStorefrontProductQueryHandler : IRequestHandler<GetStorefrontProductQuery, GetStorefrontProductResponse>
{
    private readonly IApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly IDistributedCache _cache;
    private readonly IExchangeRateService _exchangeRateService;
    private readonly ILogger<GetStorefrontProductQueryHandler> _logger;

    public GetStorefrontProductQueryHandler(
        IApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor,
        IDistributedCache cache,
        IExchangeRateService exchangeRateService,
        ILogger<GetStorefrontProductQueryHandler> logger)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
        _cache = cache;
        _exchangeRateService = exchangeRateService;
        _logger = logger;
    }

    public async Task<GetStorefrontProductResponse> Handle(GetStorefrontProductQuery request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        // Tenant bilgilerini al
        var tenant = await _dbContext.Tenants
            .AsNoTracking()
            .FirstOrDefaultAsync(t => t.Id == tenantId, cancellationToken);

        if (tenant == null)
        {
            throw new KeyNotFoundException("Tenant bulunamadı");
        }

        // Display currency
        var displayCurrency = !string.IsNullOrEmpty(request.PreferredCurrency)
            ? request.PreferredCurrency.ToUpper()
            : (tenant.SaleCurrency ?? "TRY").ToUpper();

        // Cache key
        var cacheKey = $"storefront:product:{tenantId}:{request.ProductId}:{displayCurrency}";

        // Cache kontrolü
        var cachedResult = await _cache.GetStringAsync(cacheKey, cancellationToken);
        if (!string.IsNullOrEmpty(cachedResult))
        {
            return JsonSerializer.Deserialize<GetStorefrontProductResponse>(cachedResult)!;
        }

        // Ürünü getir (sadece aktif ve published)
        var product = await _dbContext.Products
            .AsNoTracking()
            .Include(p => p.ProductCategories)
                .ThenInclude(pc => pc.Category)
            .Include(p => p.Variants)
            .Include(p => p.Images.OrderBy(img => img.Position))
            .Include(p => p.Options.OrderBy(opt => opt.Position))
            
            .FirstOrDefaultAsync(p => p.Id == request.ProductId && p.TenantId == tenantId && p.IsActive && p.Status == "Active", cancellationToken);

        if (product == null)
        {
            throw new KeyNotFoundException($"Ürün bulunamadı: {request.ProductId}");
        }

        // Currency conversion
        decimal? exchangeRate = null;
        var productCurrency = product.Currency ?? tenant.SaleCurrency ?? "TRY";
        if (productCurrency.ToUpper() != displayCurrency && displayCurrency != "TRY")
        {
            var rate = await _exchangeRateService.GetRateAsync(displayCurrency, cancellationToken);
            if (rate.HasValue && rate.Value > 0)
            {
                exchangeRate = 1 / rate.Value; // TRY'den displayCurrency'e
            }
        }
        else if (productCurrency.ToUpper() != displayCurrency && productCurrency != "TRY")
        {
            var rate = await _exchangeRateService.GetRateAsync(displayCurrency, cancellationToken);
            if (rate.HasValue)
            {
                exchangeRate = rate.Value;
            }
        }

        var price = product.Price;
        var compareAtPrice = product.CompareAtPrice;

        if (exchangeRate.HasValue && product.Currency.ToUpper() != displayCurrency)
        {
            price = product.Price * exchangeRate.Value;
            if (compareAtPrice.HasValue)
            {
                compareAtPrice = compareAtPrice.Value * exchangeRate.Value;
            }
        }

        var response = new GetStorefrontProductResponse
        {
            Id = product.Id,
            Title = product.Title,
            Description = product.Description,
            ShortDescription = product.ShortDescription,
            Slug = product.Slug,
            SKU = product.SKU,
            Price = Math.Round(price, 2, MidpointRounding.AwayFromZero),
            CompareAtPrice = compareAtPrice.HasValue
                ? Math.Round(compareAtPrice.Value, 2, MidpointRounding.AwayFromZero)
                : null,
            Currency = displayCurrency,
            InventoryQuantity = product.InventoryQuantity,
            AllowBackorder = product.AllowBackorder,
            Weight = product.Weight,
            WeightUnit = product.WeightUnit,
            RequiresShipping = product.RequiresShipping,
            IsDigital = product.IsDigital,
            IsTaxable = product.IsTaxable,
            MetaTitle = product.MetaTitle,
            MetaDescription = product.MetaDescription,
            MetaKeywords = product.MetaKeywords,
            Vendor = product.Vendor,
            ProductType = product.ProductType,
            Images = product.Images.Select(img => new StorefrontImageDto
            {
                Id = img.Id,
                OriginalUrl = img.OriginalUrl,
                ThumbnailUrl = img.ThumbnailUrl,
                SmallUrl = img.SmallUrl,
                MediumUrl = img.MediumUrl,
                LargeUrl = img.LargeUrl,
                AltText = img.AltText,
                Position = img.Position,
                IsFeatured = img.IsFeatured
            }).ToList(),
            Categories = product.ProductCategories.Select(pc => new StorefrontCategoryDto
            {
                Id = pc.Category?.Id ?? Guid.Empty,
                Name = pc.Category?.Name ?? "",
                Slug = pc.Category?.Slug ?? ""
            }).Where(c => c.Id != Guid.Empty).ToList(),
            Variants = product.Variants.Select(v => new StorefrontVariantDto
            {
                Id = v.Id,
                Title = v.Title,
                SKU = v.SKU,
                Price = exchangeRate.HasValue && product.Currency.ToUpper() != displayCurrency
                    ? Math.Round(v.Price * exchangeRate.Value, 2, MidpointRounding.AwayFromZero)
                    : v.Price,
                InventoryQuantity = v.InventoryQuantity
            }).ToList(),
            Options = product.Options.Select(opt => new StorefrontOptionDto
            {
                Id = opt.Id,
                Name = opt.Name,
                Values = opt.Values ?? new List<string>(),
                Position = opt.Position
            }).ToList(),
            Tags = product.Tags ?? new List<string>(),
            CreatedAt = product.CreatedAt
        };

        // Cache'e kaydet (10 dakika)
        await _cache.SetStringAsync(
            cacheKey,
            JsonSerializer.Serialize(response),
            new DistributedCacheEntryOptions { AbsoluteExpirationRelativeToNow = TimeSpan.FromMinutes(10) },
            cancellationToken);

        return response;
    }
}



