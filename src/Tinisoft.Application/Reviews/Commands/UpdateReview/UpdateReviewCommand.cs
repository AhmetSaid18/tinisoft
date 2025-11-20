using MediatR;

namespace Tinisoft.Application.Reviews.Commands.UpdateReview;

public class UpdateReviewCommand : IRequest<UpdateReviewResponse>
{
    public Guid ReviewId { get; set; }
    public int? Rating { get; set; } // 1-5 arası
    public string? Comment { get; set; }
    public string? Title { get; set; }
    public List<string>? ImageUrls { get; set; }
}

public class UpdateReviewResponse
{
    public Guid ReviewId { get; set; }
    public string Message { get; set; } = string.Empty;
}



