using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Infrastructure.Persistence;
using Tinisoft.Application.Common.Exceptions;
using Finbuckle.MultiTenant;
using Tinisoft.Shared.Events;
using Tinisoft.Shared.Contracts;

namespace Tinisoft.Application.Reviews.Commands.ReplyToReview;

public class ReplyToReviewCommandHandler : IRequestHandler<ReplyToReviewCommand, ReplyToReviewResponse>
{
    private readonly ApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly IEventBus _eventBus;
    private readonly ILogger<ReplyToReviewCommandHandler> _logger;

    public ReplyToReviewCommandHandler(
        ApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor,
        IEventBus eventBus,
        ILogger<ReplyToReviewCommandHandler> logger)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
        _eventBus = eventBus;
        _logger = logger;
    }

    public async Task<ReplyToReviewResponse> Handle(ReplyToReviewCommand request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        var review = await _dbContext.ProductReviews
            .FirstOrDefaultAsync(r => r.Id == request.ReviewId && r.TenantId == tenantId, cancellationToken);

        if (review == null)
        {
            throw new NotFoundException("Yorum", request.ReviewId);
        }

        // Yorum onaylı ve yayınlanmış olmalı
        if (!review.IsApproved || !review.IsPublished)
        {
            throw new BadRequestException("Sadece onaylı ve yayınlanmış yorumlara yanıt verilebilir");
        }

        // User kontrolü (tenant'a ait mi?)
        var user = await _dbContext.Users
            .FirstOrDefaultAsync(u => u.Id == request.RepliedBy, cancellationToken);

        if (user == null)
        {
            throw new NotFoundException("Kullanıcı", request.RepliedBy);
        }

        // Zaten yanıt var mı?
        if (!string.IsNullOrEmpty(review.ReplyText))
        {
            throw new BadRequestException("Bu yoruma zaten yanıt verilmiş");
        }

        review.ReplyText = request.ReplyText;
        review.RepliedBy = request.RepliedBy;
        review.RepliedAt = DateTime.UtcNow;
        review.UpdatedAt = DateTime.UtcNow;

        await _dbContext.SaveChangesAsync(cancellationToken);

        _logger.LogInformation("Reply added to review: {ReviewId} by User: {UserId}", review.Id, request.RepliedBy);

        // Event publish
        await _eventBus.PublishAsync(new ReviewRepliedEvent
        {
            ReviewId = review.Id,
            ProductId = review.ProductId,
            TenantId = tenantId,
            RepliedBy = request.RepliedBy
        }, cancellationToken);

        return new ReplyToReviewResponse
        {
            ReviewId = review.Id,
            ReplyText = review.ReplyText,
            RepliedAt = review.RepliedAt.Value,
            Message = "Yanıt başarıyla eklendi"
        };
    }
}

