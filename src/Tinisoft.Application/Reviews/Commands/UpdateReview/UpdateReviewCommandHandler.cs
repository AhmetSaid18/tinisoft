using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Application.Common.Interfaces;
using Tinisoft.Shared.Contracts;
using Tinisoft.Application.Common.Exceptions;
using Finbuckle.MultiTenant;

namespace Tinisoft.Application.Reviews.Commands.UpdateReview;

public class UpdateReviewCommandHandler : IRequestHandler<UpdateReviewCommand, UpdateReviewResponse>
{
    private readonly IApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly ILogger<UpdateReviewCommandHandler> _logger;

    public UpdateReviewCommandHandler(
        IApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor,
        ILogger<UpdateReviewCommandHandler> logger)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
        _logger = logger;
    }

    public async Task<UpdateReviewResponse> Handle(UpdateReviewCommand request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        var review = await _dbContext.ProductReviews
            .Include(r => r.Product)
            .FirstOrDefaultAsync(r => r.Id == request.ReviewId && r.TenantId == tenantId, cancellationToken);

        if (review == null)
        {
            throw new NotFoundException("Yorum", request.ReviewId);
        }

        // Yorum yayınlanmışsa ve yanıt varsa güncellenemez
        if (review.IsPublished && !string.IsNullOrEmpty(review.ReplyText))
        {
            throw new BadRequestException("Yanıt verilmiş yorumlar güncellenemez");
        }

        // Rating güncelleme
        if (request.Rating.HasValue)
        {
            if (request.Rating.Value < 1 || request.Rating.Value > 5)
            {
                throw new BadRequestException("Rating 1-5 arası olmalıdır");
            }
            review.Rating = request.Rating.Value;
        }

        // Comment güncelleme
        if (request.Comment != null)
        {
            if (request.Comment.Length > 5000)
            {
                throw new BadRequestException("Yorum en fazla 5000 karakter olabilir");
            }
            review.Comment = request.Comment;
        }

        // Title güncelleme
        if (request.Title != null)
        {
            if (request.Title.Length > 200)
            {
                throw new BadRequestException("Başlık en fazla 200 karakter olabilir");
            }
            review.Title = request.Title;
        }

        // ImageUrls güncelleme
        if (request.ImageUrls != null)
        {
            review.ImageUrls = request.ImageUrls;
        }

        // Güncelleme sonrası tekrar onay gerektir (eğer zaten onaylıysa)
        if (review.IsApproved)
        {
            review.IsApproved = false;
            review.IsPublished = false;
            _logger.LogInformation("Review {ReviewId} needs re-approval after update", review.Id);
        }

        review.UpdatedAt = DateTime.UtcNow;
        await _dbContext.SaveChangesAsync(cancellationToken);

        _logger.LogInformation("Review updated: {ReviewId}", review.Id);

        return new UpdateReviewResponse
        {
            ReviewId = review.Id,
            Message = "Yorum güncellendi, yeniden onay gerekiyor"
        };
    }
}



