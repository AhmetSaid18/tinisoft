using MediatR;

namespace Tinisoft.Application.Reviews.Commands.VoteReview;

public class VoteReviewCommand : IRequest<VoteReviewResponse>
{
    public Guid ReviewId { get; set; }
    public bool IsHelpful { get; set; } = true; // true = faydalı, false = faydalı değil
    public Guid? CustomerId { get; set; } // Opsiyonel - anonymous vote için null
}

public class VoteReviewResponse
{
    public Guid ReviewId { get; set; }
    public int HelpfulCount { get; set; }
    public int NotHelpfulCount { get; set; }
    public string Message { get; set; } = string.Empty;
}



