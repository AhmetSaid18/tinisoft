using MediatR;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Caching.Distributed;
using System.Text.Json;
using Tinisoft.Infrastructure.Persistence;
using Finbuckle.MultiTenant;

namespace Tinisoft.Application.Products.Queries.GetProduct;

public class GetProductQueryHandler : IRequestHandler<GetProductQuery, GetProductResponse>
{
    private readonly ApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly IDistributedCache _cache;
    private readonly ILogger<GetProductQueryHandler> _logger;

    public GetProductQueryHandler(
        ApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor,
        IDistributedCache cache,
        ILogger<GetProductQueryHandler> logger)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
        _cache = cache;
        _logger = logger;
    }

    public async Task<GetProductResponse> Handle(GetProductQuery request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        // Cache key
        var cacheKey = $"product:{tenantId}:{request.ProductId}";
        
        // Try cache first
        var cachedResult = await _cache.GetStringAsync(cacheKey, cancellationToken);
        if (!string.IsNullOrEmpty(cachedResult))
        {
            return JsonSerializer.Deserialize<GetProductResponse>(cachedResult)!;
        }

        var product = await _dbContext.Products
            .Include(p => p.ProductCategories)
                .ThenInclude(pc => pc.Category)
            .Include(p => p.Variants)
            .Include(p => p.Images.OrderBy(img => img.Position))
            .Include(p => p.Options.OrderBy(opt => opt.Position))
            .Include(p => p.Metafields)
            .AsSplitQuery() // Performance için split query
            .FirstOrDefaultAsync(p => p.Id == request.ProductId && p.TenantId == tenantId, cancellationToken);

        if (product == null)
        {
            throw new KeyNotFoundException($"Ürün bulunamadı: {request.ProductId}");
        }

        var response = new GetProductResponse
        {
            Id = product.Id,
            Title = product.Title,
            Description = product.Description,
            ShortDescription = product.ShortDescription,
            Slug = product.Slug,
            SKU = product.SKU,
            Barcode = product.Barcode,
            GTIN = product.GTIN,
            Price = product.Price,
            CompareAtPrice = product.CompareAtPrice,
            CostPerItem = product.CostPerItem,
            Currency = product.Currency,
            Status = product.Status,
            TrackInventory = product.TrackInventory,
            InventoryQuantity = product.InventoryQuantity,
            AllowBackorder = product.AllowBackorder,
            Weight = product.Weight,
            Length = product.Length,
            Width = product.Width,
            Height = product.Height,
            RequiresShipping = product.RequiresShipping,
            IsDigital = product.IsDigital,
            IsTaxable = product.IsTaxable,
            TaxCode = product.TaxCode,
            MetaTitle = product.MetaTitle,
            MetaDescription = product.MetaDescription,
            MetaKeywords = product.MetaKeywords,
            Vendor = product.Vendor,
            ProductType = product.ProductType,
            PublishedScope = product.PublishedScope,
            TemplateSuffix = product.TemplateSuffix,
            IsGiftCard = product.IsGiftCard,
            InventoryManagement = product.InventoryManagement,
            FulfillmentService = product.FulfillmentService,
            CountryOfOrigin = product.CountryOfOrigin,
            HSCode = product.HSCode,
            MinQuantity = product.MinQuantity,
            MaxQuantity = product.MaxQuantity,
            IncrementQuantity = product.IncrementQuantity,
            ShippingClass = product.ShippingClass,
            BarcodeFormat = product.BarcodeFormat,
            UnitPrice = product.UnitPrice,
            UnitPriceUnit = product.UnitPriceUnit,
            ChargeTaxes = product.ChargeTaxes,
            TaxCategory = product.TaxCategory,
            DefaultInventoryLocationId = product.DefaultInventoryLocationId,
            IsActive = product.IsActive,
            PublishedAt = product.PublishedAt,
            WeightUnit = product.WeightUnit,
            CreatedAt = product.CreatedAt,
            UpdatedAt = product.UpdatedAt,
            Categories = product.ProductCategories.Select(pc => new CategoryDto
            {
                Id = pc.Category!.Id,
                Name = pc.Category.Name,
                Slug = pc.Category.Slug
            }).ToList(),
            Variants = product.Variants.Select(v => new VariantDto
            {
                Id = v.Id,
                Title = v.Title,
                SKU = v.SKU,
                Price = v.Price,
                InventoryQuantity = v.InventoryQuantity
            }).ToList(),
            Images = product.Images.Select(img => new ImageDto
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
            Options = product.Options.Select(opt => new OptionDto
            {
                Id = opt.Id,
                Name = opt.Name,
                Values = opt.Values,
                Position = opt.Position
            }).ToList(),
            Metafields = product.Metafields.Select(mf => new MetafieldDto
            {
                Id = mf.Id,
                Namespace = mf.Namespace,
                Key = mf.Key,
                Value = mf.Value,
                Type = mf.Type,
                Description = mf.Description
            }).ToList(),
            Tags = product.Tags,
            Collections = product.Collections,
            SalesChannels = product.SalesChannels,
            VideoUrl = product.VideoUrl,
            VideoThumbnailUrl = product.VideoThumbnailUrl,
            CustomFields = !string.IsNullOrEmpty(product.CustomFieldsJson) 
                ? System.Text.Json.JsonSerializer.Deserialize<Dictionary<string, object>>(product.CustomFieldsJson)
                : null
        };

        // Cache for 10 minutes
        var cacheOptions = new DistributedCacheEntryOptions
        {
            AbsoluteExpirationRelativeToNow = TimeSpan.FromMinutes(10)
        };
        await _cache.SetStringAsync(cacheKey, JsonSerializer.Serialize(response), cacheOptions, cancellationToken);

        return response;
    }
}
