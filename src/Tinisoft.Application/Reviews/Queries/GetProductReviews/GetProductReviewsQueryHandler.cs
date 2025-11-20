using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Application.Common.Interfaces;
using Tinisoft.Shared.Contracts;
using Tinisoft.Application.Common.Exceptions;
using Finbuckle.MultiTenant;

namespace Tinisoft.Application.Reviews.Queries.GetProductReviews;

public class GetProductReviewsQueryHandler : IRequestHandler<GetProductReviewsQuery, GetProductReviewsResponse>
{
    private readonly IApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly ILogger<GetProductReviewsQueryHandler> _logger;

    public GetProductReviewsQueryHandler(
        IApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor,
        ILogger<GetProductReviewsQueryHandler> logger)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
        _logger = logger;
    }

    public async Task<GetProductReviewsResponse> Handle(GetProductReviewsQuery request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        // Ürün kontrolü
        var product = await _dbContext.Products
            .FirstOrDefaultAsync(p => p.Id == request.ProductId && p.TenantId == tenantId, cancellationToken);

        if (product == null)
        {
            throw new NotFoundException("Ürün", request.ProductId);
        }

        // Base query - sadece onaylı ve yayınlanmış yorumlar
        var baseQuery = _dbContext.ProductReviews
            .Where(r => r.TenantId == tenantId && 
                       r.ProductId == request.ProductId &&
                       r.IsApproved && 
                       r.IsPublished)
            .AsQueryable();

        // Filtreler
        if (request.MinRating.HasValue)
        {
            baseQuery = baseQuery.Where(r => r.Rating >= request.MinRating.Value);
        }

        if (request.MaxRating.HasValue)
        {
            baseQuery = baseQuery.Where(r => r.Rating <= request.MaxRating.Value);
        }

        if (request.IsVerifiedPurchase.HasValue)
        {
            baseQuery = baseQuery.Where(r => r.IsVerifiedPurchase == request.IsVerifiedPurchase.Value);
        }

        if (request.HasReply.HasValue)
        {
            if (request.HasReply.Value)
            {
                baseQuery = baseQuery.Where(r => !string.IsNullOrEmpty(r.ReplyText));
            }
            else
            {
                baseQuery = baseQuery.Where(r => string.IsNullOrEmpty(r.ReplyText));
            }
        }

        if (request.OnlyWithImages.HasValue && request.OnlyWithImages.Value)
        {
            baseQuery = baseQuery.Where(r => r.ImageUrls != null && r.ImageUrls.Any());
        }

        // İstatistikler (filtrelemeden önce)
        var allApprovedReviews = await _dbContext.ProductReviews
            .Where(r => r.TenantId == tenantId && 
                       r.ProductId == request.ProductId &&
                       r.IsApproved && 
                       r.IsPublished)
            .ToListAsync(cancellationToken);

        var statistics = new ReviewStatisticsDto
        {
            TotalReviews = allApprovedReviews.Count,
            AverageRating = allApprovedReviews.Any() ? allApprovedReviews.Average(r => r.Rating) : 0,
            Rating1Count = allApprovedReviews.Count(r => r.Rating == 1),
            Rating2Count = allApprovedReviews.Count(r => r.Rating == 2),
            Rating3Count = allApprovedReviews.Count(r => r.Rating == 3),
            Rating4Count = allApprovedReviews.Count(r => r.Rating == 4),
            Rating5Count = allApprovedReviews.Count(r => r.Rating == 5),
            VerifiedPurchaseCount = allApprovedReviews.Count(r => r.IsVerifiedPurchase),
            WithImagesCount = allApprovedReviews.Count(r => r.ImageUrls != null && r.ImageUrls.Any()),
            WithReplyCount = allApprovedReviews.Count(r => !string.IsNullOrEmpty(r.ReplyText))
        };

        // Sorting
        var sortBy = request.SortBy ?? "date";
        var sortOrder = request.SortOrder ?? "desc";

        switch (sortBy.ToLower())
        {
            case "rating":
                baseQuery = sortOrder.ToLower() == "asc"
                    ? baseQuery.OrderBy(r => r.Rating).ThenByDescending(r => r.CreatedAt)
                    : baseQuery.OrderByDescending(r => r.Rating).ThenByDescending(r => r.CreatedAt);
                break;
            case "helpful":
                baseQuery = sortOrder.ToLower() == "asc"
                    ? baseQuery.OrderBy(r => r.HelpfulCount).ThenByDescending(r => r.CreatedAt)
                    : baseQuery.OrderByDescending(r => r.HelpfulCount).ThenByDescending(r => r.CreatedAt);
                break;
            case "date":
            default:
                baseQuery = sortOrder.ToLower() == "asc"
                    ? baseQuery.OrderBy(r => r.CreatedAt)
                    : baseQuery.OrderByDescending(r => r.CreatedAt);
                break;
        }

        // Pagination
        var totalCount = await baseQuery.CountAsync(cancellationToken);
        var pageSize = Math.Min(request.PageSize, 100); // Max 100 per page
        var page = Math.Max(request.Page, 1);

        var reviews = await baseQuery
            .Skip((page - 1) * pageSize)
            .Take(pageSize)
            .Select(r => new ProductReviewDto
            {
                Id = r.Id,
                ProductId = r.ProductId,
                CustomerId = r.CustomerId,
                ReviewerName = r.CustomerId.HasValue ? null : r.ReviewerName, // Customer ID varsa isim gizli
                Rating = r.Rating,
                Title = r.Title,
                Comment = r.Comment,
                IsVerifiedPurchase = r.IsVerifiedPurchase,
                ImageUrls = r.ImageUrls,
                ReplyText = r.ReplyText,
                RepliedAt = r.RepliedAt,
                HelpfulCount = r.HelpfulCount,
                NotHelpfulCount = r.NotHelpfulCount,
                CreatedAt = r.CreatedAt,
                UpdatedAt = r.UpdatedAt
            })
            .ToListAsync(cancellationToken);

        return new GetProductReviewsResponse
        {
            Items = reviews,
            TotalCount = totalCount,
            Page = page,
            PageSize = pageSize,
            Statistics = statistics
        };
    }
}



