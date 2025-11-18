using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Infrastructure.Persistence;
using Tinisoft.Application.Common.Exceptions;
using Finbuckle.MultiTenant;
using Microsoft.AspNetCore.Http;

namespace Tinisoft.Application.Reviews.Commands.VoteReview;

public class VoteReviewCommandHandler : IRequestHandler<VoteReviewCommand, VoteReviewResponse>
{
    private readonly ApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly IHttpContextAccessor _httpContextAccessor;
    private readonly ILogger<VoteReviewCommandHandler> _logger;

    public VoteReviewCommandHandler(
        ApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor,
        IHttpContextAccessor httpContextAccessor,
        ILogger<VoteReviewCommandHandler> logger)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
        _httpContextAccessor = httpContextAccessor;
        _logger = logger;
    }

    public async Task<VoteReviewResponse> Handle(VoteReviewCommand request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        var review = await _dbContext.ProductReviews
            .FirstOrDefaultAsync(r => r.Id == request.ReviewId && r.TenantId == tenantId, cancellationToken);

        if (review == null)
        {
            throw new NotFoundException("Yorum", request.ReviewId);
        }

        // Yorum yayınlanmış olmalı
        if (!review.IsPublished)
        {
            throw new BadRequestException("Sadece yayınlanmış yorumlara oy verilebilir");
        }

        var ipAddress = _httpContextAccessor.HttpContext?.Connection.RemoteIpAddress?.ToString();

        // Duplicate vote kontrolü
        var existingVote = await _dbContext.Set<ReviewVote>()
            .FirstOrDefaultAsync(v => 
                v.TenantId == tenantId &&
                v.ReviewId == request.ReviewId &&
                ((request.CustomerId.HasValue && v.CustomerId == request.CustomerId.Value) ||
                 (!request.CustomerId.HasValue && !string.IsNullOrEmpty(ipAddress) &&
                  v.IpAddress != null && v.IpAddress == ipAddress)),
                cancellationToken);

        if (existingVote != null)
        {
            // Eğer aynı oy ise, oyu kaldır (toggle)
            if (existingVote.IsHelpful == request.IsHelpful)
            {
                // Oyu kaldır
                if (existingVote.IsHelpful)
                {
                    review.HelpfulCount = Math.Max(0, review.HelpfulCount - 1);
                }
                else
                {
                    review.NotHelpfulCount = Math.Max(0, review.NotHelpfulCount - 1);
                }

                _dbContext.Set<ReviewVote>().Remove(existingVote);
                
                await _dbContext.SaveChangesAsync(cancellationToken);

                return new VoteReviewResponse
                {
                    ReviewId = review.Id,
                    HelpfulCount = review.HelpfulCount,
                    NotHelpfulCount = review.NotHelpfulCount,
                    Message = "Oy kaldırıldı"
                };
            }
            else
            {
                // Farklı oy ise, eski oyu kaldır ve yeni oy ekle
                if (existingVote.IsHelpful)
                {
                    review.HelpfulCount = Math.Max(0, review.HelpfulCount - 1);
                    review.NotHelpfulCount++;
                }
                else
                {
                    review.NotHelpfulCount = Math.Max(0, review.NotHelpfulCount - 1);
                    review.HelpfulCount++;
                }

                existingVote.IsHelpful = request.IsHelpful;
                existingVote.UpdatedAt = DateTime.UtcNow;
            }
        }
        else
        {
            // Yeni oy ekle
            var vote = new ReviewVote
            {
                TenantId = tenantId,
                ReviewId = request.ReviewId,
                CustomerId = request.CustomerId,
                IpAddress = request.CustomerId.HasValue ? null : ipAddress,
                IsHelpful = request.IsHelpful
            };

            _dbContext.Set<ReviewVote>().Add(vote);

            if (request.IsHelpful)
            {
                review.HelpfulCount++;
            }
            else
            {
                review.NotHelpfulCount++;
            }
        }

        review.UpdatedAt = DateTime.UtcNow;
        await _dbContext.SaveChangesAsync(cancellationToken);

        _logger.LogInformation("Vote added to review: {ReviewId}, Helpful: {IsHelpful}", review.Id, request.IsHelpful);

        return new VoteReviewResponse
        {
            ReviewId = review.Id,
            HelpfulCount = review.HelpfulCount,
            NotHelpfulCount = review.NotHelpfulCount,
            Message = request.IsHelpful ? "Faydalı olarak işaretlendi" : "Faydalı değil olarak işaretlendi"
        };
    }
}

