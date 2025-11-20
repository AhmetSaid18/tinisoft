using MediatR;

namespace Tinisoft.Application.Reviews.Commands.ApproveReview;

public class ApproveReviewCommand : IRequest<ApproveReviewResponse>
{
    public Guid ReviewId { get; set; }
    public bool Approve { get; set; } = true; // true = onayla, false = reddet
    public string? ModerationNote { get; set; } // Red nedeni (opsiyonel)
}

public class ApproveReviewResponse
{
    public Guid ReviewId { get; set; }
    public bool IsApproved { get; set; }
    public bool IsPublished { get; set; }
    public string Message { get; set; } = string.Empty;
}



