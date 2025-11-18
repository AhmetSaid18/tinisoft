using MediatR;

namespace Tinisoft.Application.Reviews.Commands.ReplyToReview;

public class ReplyToReviewCommand : IRequest<ReplyToReviewResponse>
{
    public Guid ReviewId { get; set; }
    public string ReplyText { get; set; } = string.Empty;
    public Guid RepliedBy { get; set; } // User ID (mağaza sahibi/admin)
}

public class ReplyToReviewResponse
{
    public Guid ReviewId { get; set; }
    public string ReplyText { get; set; } = string.Empty;
    public DateTime RepliedAt { get; set; }
    public string Message { get; set; } = string.Empty;
}

