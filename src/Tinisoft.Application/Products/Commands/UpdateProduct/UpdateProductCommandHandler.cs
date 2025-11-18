using MediatR;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Caching.Distributed;
using Tinisoft.Domain.Entities;
using Tinisoft.Infrastructure.Persistence;
using Tinisoft.Application.Products.Services;
using Tinisoft.Application.ExchangeRates.Services;
using Tinisoft.Shared.Events;
using Tinisoft.Shared.Contracts;
using Finbuckle.MultiTenant;

namespace Tinisoft.Application.Products.Commands.UpdateProduct;

public class UpdateProductCommandHandler : IRequestHandler<UpdateProductCommand, UpdateProductResponse>
{
    private readonly ApplicationDbContext _dbContext;
    private readonly IEventBus _eventBus;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly IDistributedCache _cache;
    private readonly IMeilisearchService _meilisearchService;
    private readonly IExchangeRateService _exchangeRateService;
    private readonly ILogger<UpdateProductCommandHandler> _logger;

    public UpdateProductCommandHandler(
        ApplicationDbContext dbContext,
        IEventBus eventBus,
        IMultiTenantContextAccessor tenantAccessor,
        IDistributedCache cache,
        IMeilisearchService meilisearchService,
        IExchangeRateService exchangeRateService,
        ILogger<UpdateProductCommandHandler> logger)
    {
        _dbContext = dbContext;
        _eventBus = eventBus;
        _tenantAccessor = tenantAccessor;
        _cache = cache;
        _meilisearchService = meilisearchService;
        _exchangeRateService = exchangeRateService;
        _logger = logger;
    }

    public async Task<UpdateProductResponse> Handle(UpdateProductCommand request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        // Tenant bilgisini çek (currency ayarları için)
        var tenant = await _dbContext.Tenants.FirstOrDefaultAsync(t => t.Id == tenantId, cancellationToken);
        if (tenant == null)
        {
            throw new InvalidOperationException("Tenant bulunamadı");
        }

        var product = await _dbContext.Products
            .FirstOrDefaultAsync(p => p.Id == request.ProductId && p.TenantId == tenantId, cancellationToken);

        if (product == null)
        {
            throw new KeyNotFoundException($"Ürün bulunamadı: {request.ProductId}");
        }

        // Currency conversion logic (eğer purchase currency değiştiyse)
        if (request.PurchaseCurrency != null || request.PurchasePrice.HasValue)
        {
            var purchaseCurrency = request.PurchaseCurrency ?? product.PurchaseCurrency;
            var purchasePrice = request.PurchasePrice ?? product.PurchasePrice;
            var autoConvert = request.AutoConvertSalePrice ?? product.AutoConvertSalePrice;
            var saleCurrency = product.Currency ?? tenant.SaleCurrency ?? "TRY";

            if (!string.IsNullOrEmpty(purchaseCurrency) && 
                purchasePrice.HasValue && 
                autoConvert &&
                purchaseCurrency.ToUpper() != saleCurrency.ToUpper())
            {
                // Exchange rate getir (margin ile birlikte)
                var effectiveRate = await _exchangeRateService.GetEffectiveRateAsync(
                    purchaseCurrency, 
                    tenant.CurrencyMarginPercent, 
                    cancellationToken);

                if (effectiveRate.HasValue)
                {
                    // Purchase price'ı sale currency'ye çevir
                    var convertedPrice = purchasePrice.Value * effectiveRate.Value;
                    product.Price = convertedPrice;
                    product.ExchangeRateAtPurchase = effectiveRate.Value;
                    
                    _logger.LogInformation(
                        "Product price updated and converted: {PurchasePrice} {PurchaseCurrency} = {SalePrice} {SaleCurrency} (Rate: {Rate})",
                        purchasePrice.Value, purchaseCurrency, convertedPrice, saleCurrency, effectiveRate.Value);
                }
            }
        }

        // Update fields
        if (!string.IsNullOrEmpty(request.Title)) product.Title = request.Title;
        if (request.Description != null) product.Description = request.Description;
        if (!string.IsNullOrEmpty(request.Slug)) product.Slug = request.Slug;
        if (request.SKU != null) product.SKU = request.SKU;
        if (request.Price.HasValue && (request.PurchaseCurrency == null && !request.PurchasePrice.HasValue)) 
            product.Price = request.Price.Value; // Sadece Price güncelleniyorsa (currency conversion yoksa)
        if (request.CompareAtPrice.HasValue) product.CompareAtPrice = request.CompareAtPrice;
        if (request.CostPerItem.HasValue) product.CostPerItem = request.CostPerItem.Value;
        
        // Multi-currency fields
        if (request.PurchaseCurrency != null) product.PurchaseCurrency = request.PurchaseCurrency;
        if (request.PurchasePrice.HasValue) product.PurchasePrice = request.PurchasePrice;
        if (request.AutoConvertSalePrice.HasValue) product.AutoConvertSalePrice = request.AutoConvertSalePrice.Value;
        if (request.TrackInventory.HasValue) product.TrackInventory = request.TrackInventory.Value;
        if (request.InventoryQuantity.HasValue) product.InventoryQuantity = request.InventoryQuantity;
        if (request.IsActive.HasValue) product.IsActive = request.IsActive.Value;
        
        // SEO fields
        if (request.MetaTitle != null) product.MetaTitle = request.MetaTitle;
        if (request.MetaDescription != null) product.MetaDescription = request.MetaDescription;
        if (request.MetaKeywords != null) product.MetaKeywords = request.MetaKeywords;
        if (request.OgTitle != null) product.OgTitle = request.OgTitle;
        if (request.OgDescription != null) product.OgDescription = request.OgDescription;
        if (request.OgImage != null) product.OgImage = request.OgImage;
        if (request.OgType != null) product.OgType = request.OgType;
        if (request.TwitterCard != null) product.TwitterCard = request.TwitterCard;
        if (request.TwitterTitle != null) product.TwitterTitle = request.TwitterTitle;
        if (request.TwitterDescription != null) product.TwitterDescription = request.TwitterDescription;
        if (request.TwitterImage != null) product.TwitterImage = request.TwitterImage;
        if (request.CanonicalUrl != null) product.CanonicalUrl = request.CanonicalUrl;
        
        if (request.FeaturedImageUrl != null) product.FeaturedImageUrl = request.FeaturedImageUrl;
        if (request.ImageUrls != null) product.ImageUrls = request.ImageUrls;

        product.UpdatedAt = DateTime.UtcNow;

        await _dbContext.SaveChangesAsync(cancellationToken);

        // Cache invalidation - Ürün güncellendiğinde cache'leri temizle
        await InvalidateProductCacheAsync(tenantId, product.Id, cancellationToken);

        // Meilisearch update (background)
        _ = Task.Run(async () =>
        {
            try
            {
                await _meilisearchService.UpdateProductAsync(product, cancellationToken);
            }
            catch (Exception ex)
            {
                _logger.LogWarning(ex, "Meilisearch update failed for product: {ProductId}", product.Id);
            }
        }, cancellationToken);

        // Event publish
        await _eventBus.PublishAsync(new ProductUpdatedEvent
        {
            ProductId = product.Id,
            TenantId = tenantId,
            Changes = "Product updated"
        }, cancellationToken);

        _logger.LogInformation("Product updated: {ProductId}", product.Id);

        return new UpdateProductResponse
        {
            ProductId = product.Id,
            Title = product.Title
        };
    }

    private async Task InvalidateProductCacheAsync(Guid tenantId, Guid productId, CancellationToken cancellationToken)
    {
        try
        {
            // Product detail cache
            var productCacheKey = $"product:{tenantId}:{productId}";
            await _cache.RemoveAsync(productCacheKey, cancellationToken);

            // Product list cache'leri (pattern ile silmek için tüm olası kombinasyonları temizle)
            // Basit yaklaşım: Tüm product list cache'lerini temizle (tenant bazlı)
            // İleride Redis pattern delete ile optimize edilebilir
            var cacheKeys = new[]
            {
                $"products:list:{tenantId}:*" // Pattern - Redis'te SCAN kullanılabilir
            };

            // Şimdilik sadece product detail cache'i temizliyoruz
            // List cache'leri TTL ile otomatik expire olacak
            _logger.LogInformation("Cache invalidated for product: {ProductId}", productId);
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "Cache invalidation error for product: {ProductId}", productId);
            // Cache hatası kritik değil, devam et
        }
    }
}

