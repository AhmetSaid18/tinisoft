using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Domain.Entities;
using Tinisoft.Infrastructure.Persistence;
using Tinisoft.Infrastructure.Services;
using Tinisoft.Application.Products.Services;
using Tinisoft.Shared.Events;
using Tinisoft.Shared.Contracts;
using Finbuckle.MultiTenant;
using System.Text;

namespace Tinisoft.Application.Products.Commands.CreateProduct;

public class CreateProductCommandHandler : IRequestHandler<CreateProductCommand, CreateProductResponse>
{
    private readonly ApplicationDbContext _dbContext;
    private readonly IEventBus _eventBus;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly IImageProcessingService _imageProcessingService;
    private readonly IMeilisearchService _meilisearchService;
    private readonly ILogger<CreateProductCommandHandler> _logger;

    public CreateProductCommandHandler(
        ApplicationDbContext dbContext,
        IEventBus eventBus,
        IMultiTenantContextAccessor tenantAccessor,
        IImageProcessingService imageProcessingService,
        IMeilisearchService meilisearchService,
        ILogger<CreateProductCommandHandler> logger)
    {
        _dbContext = dbContext;
        _eventBus = eventBus;
        _tenantAccessor = tenantAccessor;
        _imageProcessingService = imageProcessingService;
        _meilisearchService = meilisearchService;
        _logger = logger;
    }

    public async Task<CreateProductResponse> Handle(CreateProductCommand request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        // Slug kontrolü
        var existingProduct = await _dbContext.Products
            .FirstOrDefaultAsync(p => p.TenantId == tenantId && p.Slug == request.Slug, cancellationToken);

        if (existingProduct != null)
        {
            throw new InvalidOperationException($"Slug '{request.Slug}' zaten kullanılıyor");
        }

        var product = new Product
        {
            TenantId = tenantId,
            Title = request.Title,
            Description = request.Description,
            ShortDescription = request.ShortDescription,
            Slug = request.Slug,
            SKU = request.SKU,
            Barcode = request.Barcode,
            GTIN = request.GTIN,
            Price = request.Price,
            CompareAtPrice = request.CompareAtPrice,
            CostPerItem = request.CostPerItem,
            Currency = request.Currency,
            Status = request.Status,
            IsActive = request.IsActive,
            TrackInventory = request.TrackInventory,
            InventoryQuantity = request.TrackInventory ? request.InventoryQuantity : null,
            AllowBackorder = request.AllowBackorder,
            InventoryPolicy = request.InventoryPolicy,
            Weight = request.Weight,
            WeightUnit = request.WeightUnit,
            Length = request.Length,
            Width = request.Width,
            Height = request.Height,
            RequiresShipping = request.RequiresShipping,
            IsDigital = request.IsDigital,
            ShippingWeight = request.ShippingWeight,
            IsTaxable = request.IsTaxable,
            TaxCode = request.TaxCode,
            MetaTitle = request.MetaTitle,
            MetaDescription = request.MetaDescription,
            MetaKeywords = request.MetaKeywords,
            OgTitle = request.OgTitle,
            OgDescription = request.OgDescription,
            OgImage = request.OgImage,
            OgType = request.OgType,
            TwitterCard = request.TwitterCard,
            TwitterTitle = request.TwitterTitle,
            TwitterDescription = request.TwitterDescription,
            TwitterImage = request.TwitterImage,
            CanonicalUrl = request.CanonicalUrl,
            Vendor = request.Vendor,
            ProductType = request.ProductType,
            Tags = request.Tags,
            Collections = request.Collections,
            PublishedScope = request.PublishedScope,
            TemplateSuffix = request.TemplateSuffix,
            IsGiftCard = request.IsGiftCard,
            InventoryManagement = request.InventoryManagement,
            FulfillmentService = request.FulfillmentService,
            CountryOfOrigin = request.CountryOfOrigin,
            HSCode = request.HSCode,
            MinQuantity = request.MinQuantity,
            MaxQuantity = request.MaxQuantity,
            IncrementQuantity = request.IncrementQuantity,
            SalesChannels = request.SalesChannels,
            VideoUrl = request.VideoUrl,
            VideoThumbnailUrl = request.VideoThumbnailUrl,
            CustomFieldsJson = request.CustomFields != null ? System.Text.Json.JsonSerializer.Serialize(request.CustomFields) : null,
            DefaultInventoryLocationId = request.DefaultInventoryLocationId,
            BarcodeFormat = request.BarcodeFormat,
            UnitPrice = request.UnitPrice,
            UnitPriceUnit = request.UnitPriceUnit,
            ChargeTaxes = request.ChargeTaxes,
            TaxCategory = request.TaxCategory,
            ShippingClass = request.ShippingClass,
            PublishedAt = request.Status == "Active" ? DateTime.UtcNow : null
        };

        _dbContext.Products.Add(product);

        // Process images
        if (request.Images.Any())
        {
            for (int i = 0; i < request.Images.Count; i++)
            {
                var imageInput = request.Images[i];
                ProcessedImageResult? processedImage = null;

                try
                {
                    if (!string.IsNullOrEmpty(imageInput.Base64Data))
                    {
                        // Base64'ten image process et
                        var imageBytes = Convert.FromBase64String(imageInput.Base64Data.Replace("data:image/jpeg;base64,", "").Replace("data:image/png;base64,", ""));
                        using var imageStream = new MemoryStream(imageBytes);
                        var fileName = $"{product.Id}_{i}_{Guid.NewGuid():N}.jpg";
                        processedImage = await _imageProcessingService.ProcessImageAsync(imageStream, fileName, cancellationToken);
                    }
                    else if (!string.IsNullOrEmpty(imageInput.Url))
                    {
                        // URL'den image process et
                        var fileName = $"{product.Id}_{i}_{Guid.NewGuid():N}.jpg";
                        processedImage = await _imageProcessingService.ProcessImageFromUrlAsync(imageInput.Url, fileName, cancellationToken);
                    }

                    if (processedImage != null)
                    {
                        var productImage = new ProductImage
                        {
                            ProductId = product.Id,
                            Position = imageInput.Position,
                            AltText = imageInput.AltText ?? product.Title,
                            OriginalUrl = processedImage.OriginalUrl,
                            OriginalSizeBytes = processedImage.OriginalSizeBytes,
                            OriginalWidth = processedImage.OriginalWidth,
                            OriginalHeight = processedImage.OriginalHeight,
                            ThumbnailUrl = processedImage.ThumbnailUrl,
                            SmallUrl = processedImage.SmallUrl,
                            MediumUrl = processedImage.MediumUrl,
                            LargeUrl = processedImage.LargeUrl,
                            IsFeatured = imageInput.IsFeatured
                        };
                        _dbContext.Set<ProductImage>().Add(productImage);
                    }
                }
                catch (Exception ex)
                {
                    _logger.LogError(ex, "Error processing image {Index} for product {ProductId}", i, product.Id);
                    // Continue with other images
                }
            }
        }

        // Add options
        if (request.Options.Any())
        {
            foreach (var optionDto in request.Options)
            {
                var productOption = new ProductOption
                {
                    ProductId = product.Id,
                    Name = optionDto.Name,
                    Values = optionDto.Values,
                    Position = optionDto.Position
                };
                _dbContext.Set<ProductOption>().Add(productOption);
            }
        }

        // Add metafields
        if (request.Metafields.Any())
        {
            foreach (var metafieldDto in request.Metafields)
            {
                var metafield = new ProductMetafield
                {
                    ProductId = product.Id,
                    Namespace = metafieldDto.Namespace,
                    Key = metafieldDto.Key,
                    Value = metafieldDto.Value,
                    Type = metafieldDto.Type,
                    Description = metafieldDto.Description
                };
                _dbContext.Set<ProductMetafield>().Add(metafield);
            }
        }

        // Kategorileri ekle
        if (request.CategoryIds.Any())
        {
            foreach (var categoryId in request.CategoryIds)
            {
                var productCategory = new ProductCategory
                {
                    ProductId = product.Id,
                    CategoryId = categoryId,
                    IsPrimary = request.CategoryIds.IndexOf(categoryId) == 0
                };
                _dbContext.ProductCategories.Add(productCategory);
            }
        }

        // Depo bazlı stok ekle
        if (request.WarehouseInventories.Any())
        {
            foreach (var warehouseInv in request.WarehouseInventories)
            {
                // Warehouse'un bu tenant'a ait olduğunu kontrol et
                var warehouse = await _dbContext.Warehouses
                    .FirstOrDefaultAsync(w => w.Id == warehouseInv.WarehouseId && w.TenantId == tenantId, cancellationToken);

                if (warehouse == null)
                {
                    _logger.LogWarning("Warehouse {WarehouseId} not found or doesn't belong to tenant {TenantId}", 
                        warehouseInv.WarehouseId, tenantId);
                    continue;
                }

                var productInventory = new ProductInventory
                {
                    TenantId = tenantId,
                    ProductId = product.Id,
                    WarehouseId = warehouseInv.WarehouseId,
                    Quantity = warehouseInv.Quantity,
                    ReservedQuantity = 0,
                    MinStockLevel = warehouseInv.MinStockLevel,
                    MaxStockLevel = warehouseInv.MaxStockLevel,
                    Cost = warehouseInv.Cost,
                    Location = warehouseInv.Location,
                    IsActive = true
                };
                _dbContext.Set<ProductInventory>().Add(productInventory);
            }

            // Toplam stok miktarını hesapla ve product'a yaz
            var totalQuantity = request.WarehouseInventories.Sum(wi => wi.Quantity);
            if (request.TrackInventory && totalQuantity > 0)
            {
                product.InventoryQuantity = totalQuantity;
            }
        }

        await _dbContext.SaveChangesAsync(cancellationToken);

        // Meilisearch index (background - await etme)
        _ = Task.Run(async () =>
        {
            try
            {
                await _meilisearchService.IndexProductAsync(product, cancellationToken);
            }
            catch (Exception ex)
            {
                _logger.LogWarning(ex, "Meilisearch indexing failed for product: {ProductId}", product.Id);
            }
        }, cancellationToken);

        // Event publish
        await _eventBus.PublishAsync(new ProductCreatedEvent
        {
            ProductId = product.Id,
            TenantId = tenantId,
            Title = product.Title,
            SKU = product.SKU ?? string.Empty
        }, cancellationToken);

        _logger.LogInformation("Product created: {ProductId} - {Title}", product.Id, product.Title);

        return new CreateProductResponse
        {
            ProductId = product.Id,
            Title = product.Title
        };
    }
}

