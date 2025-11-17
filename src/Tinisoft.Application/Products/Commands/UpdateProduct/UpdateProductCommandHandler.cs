using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Domain.Entities;
using Tinisoft.Infrastructure.Persistence;
using Tinisoft.Shared.Events;
using Tinisoft.Shared.Contracts;
using Finbuckle.MultiTenant;

namespace Tinisoft.Application.Products.Commands.UpdateProduct;

public class UpdateProductCommandHandler : IRequestHandler<UpdateProductCommand, UpdateProductResponse>
{
    private readonly ApplicationDbContext _dbContext;
    private readonly IEventBus _eventBus;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly ILogger<UpdateProductCommandHandler> _logger;

    public UpdateProductCommandHandler(
        ApplicationDbContext dbContext,
        IEventBus eventBus,
        IMultiTenantContextAccessor tenantAccessor,
        ILogger<UpdateProductCommandHandler> logger)
    {
        _dbContext = dbContext;
        _eventBus = eventBus;
        _tenantAccessor = tenantAccessor;
        _logger = logger;
    }

    public async Task<UpdateProductResponse> Handle(UpdateProductCommand request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        var product = await _dbContext.Products
            .FirstOrDefaultAsync(p => p.Id == request.ProductId && p.TenantId == tenantId, cancellationToken);

        if (product == null)
        {
            throw new KeyNotFoundException($"Ürün bulunamadı: {request.ProductId}");
        }

        // Update fields
        if (!string.IsNullOrEmpty(request.Title)) product.Title = request.Title;
        if (request.Description != null) product.Description = request.Description;
        if (!string.IsNullOrEmpty(request.Slug)) product.Slug = request.Slug;
        if (request.SKU != null) product.SKU = request.SKU;
        if (request.Price.HasValue) product.Price = request.Price.Value;
        if (request.CompareAtPrice.HasValue) product.CompareAtPrice = request.CompareAtPrice;
        if (request.CostPerItem.HasValue) product.CostPerItem = request.CostPerItem.Value;
        if (request.TrackInventory.HasValue) product.TrackInventory = request.TrackInventory.Value;
        if (request.InventoryQuantity.HasValue) product.InventoryQuantity = request.InventoryQuantity;
        if (request.IsActive.HasValue) product.IsActive = request.IsActive.Value;
        if (request.MetaTitle != null) product.MetaTitle = request.MetaTitle;
        if (request.MetaDescription != null) product.MetaDescription = request.MetaDescription;
        if (request.FeaturedImageUrl != null) product.FeaturedImageUrl = request.FeaturedImageUrl;
        if (request.ImageUrls != null) product.ImageUrls = request.ImageUrls;

        product.UpdatedAt = DateTime.UtcNow;

        await _dbContext.SaveChangesAsync(cancellationToken);

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
}

