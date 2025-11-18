using MediatR;

namespace Tinisoft.Application.Reviews.Queries.GetProductReviews;

public class GetProductReviewsQuery : IRequest<GetProductReviewsResponse>
{
    public Guid ProductId { get; set; }
    public int Page { get; set; } = 1;
    public int PageSize { get; set; } = 20;
    public string? SortBy { get; set; } // "rating", "date", "helpful" (default: date)
    public string? SortOrder { get; set; } // "asc", "desc" (default: desc)
    public int? MinRating { get; set; } // Minimum rating filtreleme (1-5)
    public int? MaxRating { get; set; } // Maximum rating filtreleme (1-5)
    public bool? IsVerifiedPurchase { get; set; } // Sadece doğrulanmış satın almalar
    public bool? HasReply { get; set; } // Sadece yanıt verilmiş yorumlar
    public bool? OnlyWithImages { get; set; } // Sadece fotoğraflı yorumlar
}

public class GetProductReviewsResponse
{
    public List<ProductReviewDto> Items { get; set; } = new();
    public int TotalCount { get; set; }
    public int Page { get; set; }
    public int PageSize { get; set; }
    public int TotalPages => (int)Math.Ceiling(TotalCount / (double)PageSize);
    public ReviewStatisticsDto Statistics { get; set; } = new();
}

public class ProductReviewDto
{
    public Guid Id { get; set; }
    public Guid ProductId { get; set; }
    public Guid? CustomerId { get; set; }
    public string? ReviewerName { get; set; }
    public int Rating { get; set; }
    public string? Title { get; set; }
    public string? Comment { get; set; }
    public bool IsVerifiedPurchase { get; set; }
    public List<string> ImageUrls { get; set; } = new();
    public string? ReplyText { get; set; }
    public DateTime? RepliedAt { get; set; }
    public int HelpfulCount { get; set; }
    public int NotHelpfulCount { get; set; }
    public DateTime CreatedAt { get; set; }
    public DateTime? UpdatedAt { get; set; }
}

public class ReviewStatisticsDto
{
    public double AverageRating { get; set; }
    public int TotalReviews { get; set; }
    public int Rating1Count { get; set; }
    public int Rating2Count { get; set; }
    public int Rating3Count { get; set; }
    public int Rating4Count { get; set; }
    public int Rating5Count { get; set; }
    public int VerifiedPurchaseCount { get; set; }
    public int WithImagesCount { get; set; }
    public int WithReplyCount { get; set; }
}

