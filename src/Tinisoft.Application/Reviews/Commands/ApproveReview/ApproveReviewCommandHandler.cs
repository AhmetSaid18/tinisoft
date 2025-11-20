using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Application.Common.Interfaces;
using Tinisoft.Shared.Contracts;
using Tinisoft.Application.Common.Exceptions;
using Finbuckle.MultiTenant;
using Tinisoft.Shared.Events;
using Tinisoft.Shared.Contracts;

namespace Tinisoft.Application.Reviews.Commands.ApproveReview;

public class ApproveReviewCommandHandler : IRequestHandler<ApproveReviewCommand, ApproveReviewResponse>
{
    private readonly IApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly IEventBus _eventBus;
    private readonly ILogger<ApproveReviewCommandHandler> _logger;

    public ApproveReviewCommandHandler(
        IApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor,
        IEventBus eventBus,
        ILogger<ApproveReviewCommandHandler> logger)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
        _eventBus = eventBus;
        _logger = logger;
    }

    public async Task<ApproveReviewResponse> Handle(ApproveReviewCommand request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        var review = await _dbContext.ProductReviews
            .Include(r => r.Product)
            .FirstOrDefaultAsync(r => r.Id == request.ReviewId && r.TenantId == tenantId, cancellationToken);

        if (review == null)
        {
            throw new NotFoundException("Yorum", request.ReviewId);
        }

        if (request.Approve)
        {
            // Onayla
            review.IsApproved = true;
            review.IsPublished = true;
            review.ModerationNote = null;
            
            // Ürünün ortalama rating'ini güncelle (background job olabilir ama şimdilik direkt yapalım)
            await UpdateProductRatingAsync(review.ProductId, tenantId, cancellationToken);

            _logger.LogInformation("Review approved: {ReviewId} for Product: {ProductId}", review.Id, review.ProductId);

            // Event publish
            await _eventBus.PublishAsync(new ReviewApprovedEvent
            {
                ReviewId = review.Id,
                ProductId = review.ProductId,
                TenantId = tenantId,
                Rating = review.Rating
            }, cancellationToken);
        }
        else
        {
            // Reddet
            review.IsApproved = false;
            review.IsPublished = false;
            review.ModerationNote = request.ModerationNote;

            _logger.LogInformation("Review rejected: {ReviewId} for Product: {ProductId}", review.Id, review.ProductId);

            // Event publish
            await _eventBus.PublishAsync(new ReviewRejectedEvent
            {
                ReviewId = review.Id,
                ProductId = review.ProductId,
                TenantId = tenantId,
                ModerationNote = request.ModerationNote
            }, cancellationToken);
        }

        review.UpdatedAt = DateTime.UtcNow;
        await _dbContext.SaveChangesAsync(cancellationToken);

        return new ApproveReviewResponse
        {
            ReviewId = review.Id,
            IsApproved = review.IsApproved,
            IsPublished = review.IsPublished,
            Message = request.Approve ? "Yorum onaylandı ve yayınlandı" : "Yorum reddedildi"
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
            // Şimdilik sadece log atalım
            _logger.LogInformation("Product {ProductId} - Average Rating: {Rating}, Total Reviews: {Count}", 
                productId, averageRating, totalReviews);
        }
    }
}



