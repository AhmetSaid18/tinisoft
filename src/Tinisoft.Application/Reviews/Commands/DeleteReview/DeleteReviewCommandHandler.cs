using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Application.Common.Interfaces;
using Tinisoft.Shared.Contracts;
using Tinisoft.Application.Common.Exceptions;
using Finbuckle.MultiTenant;
using Tinisoft.Shared.Events;
using Tinisoft.Shared.Contracts;

namespace Tinisoft.Application.Reviews.Commands.DeleteReview;

public class DeleteReviewCommandHandler : IRequestHandler<DeleteReviewCommand, DeleteReviewResponse>
{
    private readonly IApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly IEventBus _eventBus;
    private readonly ILogger<DeleteReviewCommandHandler> _logger;

    public DeleteReviewCommandHandler(
        IApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor,
        IEventBus eventBus,
        ILogger<DeleteReviewCommandHandler> logger)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
        _eventBus = eventBus;
        _logger = logger;
    }

    public async Task<DeleteReviewResponse> Handle(DeleteReviewCommand request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        var review = await _dbContext.ProductReviews
            .Include(r => r.Product)
            .FirstOrDefaultAsync(r => r.Id == request.ReviewId && r.TenantId == tenantId, cancellationToken);

        if (review == null)
        {
            throw new NotFoundException("Yorum", request.ReviewId);
        }

        var productId = review.ProductId;
        var rating = review.Rating;

        // İlişkili vote'ları sil (cascade delete)
        var votes = await _dbContext.Set<Entities.ReviewVote>()
            .Where(v => v.TenantId == tenantId && v.ReviewId == request.ReviewId)
            .ToListAsync(cancellationToken);

        if (votes.Any())
        {
            _dbContext.Set<Entities.ReviewVote>().RemoveRange(votes);
        }

        // Yorumu sil
        _dbContext.ProductReviews.Remove(review);
        await _dbContext.SaveChangesAsync(cancellationToken);

        _logger.LogInformation("Review deleted: {ReviewId} for Product: {ProductId}", review.Id, productId);

        // Event publish
        await _eventBus.PublishAsync(new ReviewDeletedEvent
        {
            ReviewId = request.ReviewId,
            ProductId = productId,
            TenantId = tenantId,
            Rating = rating
        }, cancellationToken);

        // Ürünün ortalama rating'ini güncelle (silme sonrası)
        await UpdateProductRatingAsync(productId, tenantId, cancellationToken);

        return new DeleteReviewResponse
        {
            ReviewId = request.ReviewId,
            Success = true,
            Message = "Yorum başarıyla silindi"
        };
    }

    private async Task UpdateProductRatingAsync(Guid productId, Guid tenantId, CancellationToken cancellationToken)
    {
        // Onaylı ve yayınlanmış yorumların ortalama rating'ini hesapla
        var approvedReviews = await _dbContext.ProductReviews
            .Where(r => r.ProductId == productId && 
                       r.TenantId == tenantId &&
                       r.IsApproved && 
                       r.IsPublished)
            .ToListAsync(cancellationToken);

        if (approvedReviews.Any())
        {
            var averageRating = approvedReviews.Average(r => r.Rating);
            var totalReviews = approvedReviews.Count;
            
            // TODO: Product entity'ye AverageRating ve TotalReviews field'ları eklenebilir
            _logger.LogInformation("Product {ProductId} - Average Rating: {Rating}, Total Reviews: {Count}", 
                productId, averageRating, totalReviews);
        }
        else
        {
            _logger.LogInformation("Product {ProductId} - No approved reviews remaining", productId);
        }
    }
}



