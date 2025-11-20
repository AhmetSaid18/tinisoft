using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Domain.Entities;
using Tinisoft.Application.Common.Interfaces;
using Tinisoft.Shared.Contracts;
using Finbuckle.MultiTenant;
using Tinisoft.Application.Common.Exceptions;
using Tinisoft.Shared.Events;
using Tinisoft.Shared.Contracts;

namespace Tinisoft.Application.Reviews.Commands.CreateReview;

public class CreateReviewCommandHandler : IRequestHandler<CreateReviewCommand, CreateReviewResponse>
{
    private readonly IApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly IEventBus _eventBus;
    private readonly ILogger<CreateReviewCommandHandler> _logger;

    public CreateReviewCommandHandler(
        IApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor,
        IEventBus eventBus,
        ILogger<CreateReviewCommandHandler> logger)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
        _eventBus = eventBus;
        _logger = logger;
    }

    public async Task<CreateReviewResponse> Handle(CreateReviewCommand request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        // Ürünü kontrol et
        var product = await _dbContext.Products
            .FirstOrDefaultAsync(p => p.Id == request.ProductId && p.TenantId == tenantId, cancellationToken);

        if (product == null)
        {
            throw new NotFoundException("Ürün", request.ProductId);
        }

        // Ürün aktif mi?
        if (!product.IsActive || product.Status != "Active")
        {
            throw new BadRequestException("Aktif olmayan ürün için yorum yapılamaz");
        }

        // Müşteri kontrolü (eğer CustomerId varsa)
        Customer? customer = null;
        if (request.CustomerId.HasValue)
        {
            customer = await _dbContext.Customers
                .FirstOrDefaultAsync(c => c.Id == request.CustomerId.Value && c.TenantId == tenantId, cancellationToken);

            if (customer == null)
            {
                throw new NotFoundException("Müşteri", request.CustomerId.Value);
            }

            if (!customer.IsActive)
            {
                throw new BadRequestException("Aktif olmayan müşteri yorum yapamaz");
            }
        }

        // Order verification (eğer OrderId varsa)
        bool isVerifiedPurchase = false;
        if (request.OrderId.HasValue)
        {
            var order = await _dbContext.Orders
                .Include(o => o.OrderItems)
                .FirstOrDefaultAsync(o => o.Id == request.OrderId.Value && o.TenantId == tenantId, cancellationToken);

            if (order != null)
            {
                // Müşteri bu ürünü bu siparişte satın aldı mı?
                var hasProductInOrder = order.OrderItems.Any(oi => oi.ProductId == request.ProductId);
                
                if (hasProductInOrder)
                {
                    isVerifiedPurchase = true;
                    
                    // Aynı müşteri mi kontrolü
                    if (request.CustomerId.HasValue && order.CustomerId == request.CustomerId.Value)
                    {
                        isVerifiedPurchase = true;
                    }
                    else if (!request.CustomerId.HasValue && 
                             !string.IsNullOrEmpty(request.ReviewerEmail) &&
                             order.CustomerEmail.Equals(request.ReviewerEmail, StringComparison.OrdinalIgnoreCase))
                    {
                        isVerifiedPurchase = true;
                    }
                }
            }
        }

        // Müşteri bu ürüne daha önce yorum yapmış mı? (tekrar yorum engelleme - isteğe bağlı)
        var existingReview = await _dbContext.ProductReviews
            .FirstOrDefaultAsync(pr => 
                pr.TenantId == tenantId &&
                pr.ProductId == request.ProductId &&
                ((request.CustomerId.HasValue && pr.CustomerId == request.CustomerId.Value) ||
                 (!request.CustomerId.HasValue && !string.IsNullOrEmpty(request.ReviewerEmail) &&
                  pr.ReviewerEmail != null && pr.ReviewerEmail.Equals(request.ReviewerEmail, StringComparison.OrdinalIgnoreCase))),
                cancellationToken);

        if (existingReview != null)
        {
            throw new BadRequestException("Bu ürün için zaten bir yorumunuz bulunmaktadır");
        }

        // Review oluştur
        var review = new ProductReview
        {
            TenantId = tenantId,
            ProductId = request.ProductId,
            CustomerId = request.CustomerId,
            ReviewerName = request.CustomerId.HasValue ? null : request.ReviewerName,
            ReviewerEmail = request.CustomerId.HasValue ? null : request.ReviewerEmail,
            Rating = request.Rating,
            Comment = request.Comment,
            Title = request.Title,
            OrderId = request.OrderId,
            IsVerifiedPurchase = isVerifiedPurchase,
            ImageUrls = request.ImageUrls,
            ReviewType = "Product",
            IsApproved = false, // İlk başta onay bekliyor (moderasyon)
            IsPublished = false
        };

        // TODO: Tenant ayarlarına göre otomatik onay kontrolü
        // Örneğin: Tenant.AutoApproveReviews == true ise otomatik onayla
        // Şimdilik manuel onay gerekiyor

        _dbContext.ProductReviews.Add(review);
        await _dbContext.SaveChangesAsync(cancellationToken);

        _logger.LogInformation("Review created: {ReviewId} for Product: {ProductId}", review.Id, request.ProductId);

        // Event publish
        await _eventBus.PublishAsync(new ReviewCreatedEvent
        {
            ReviewId = review.Id,
            ProductId = review.ProductId,
            TenantId = tenantId,
            Rating = review.Rating,
            CustomerId = review.CustomerId
        }, cancellationToken);

        return new CreateReviewResponse
        {
            ReviewId = review.Id,
            IsApproved = review.IsApproved,
            Message = review.IsApproved 
                ? "Yorumunuz onaylandı ve yayınlandı" 
                : "Yorumunuz alındı, onay bekliyor"
        };
    }
}



