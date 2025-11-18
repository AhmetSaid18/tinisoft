using MediatR;

namespace Tinisoft.Application.Reviews.Commands.DeleteReview;

public class DeleteReviewCommand : IRequest<DeleteReviewResponse>
{
    public Guid ReviewId { get; set; }
}

public class DeleteReviewResponse
{
    public Guid ReviewId { get; set; }
    public bool Success { get; set; }
    public string Message { get; set; } = string.Empty;
}

