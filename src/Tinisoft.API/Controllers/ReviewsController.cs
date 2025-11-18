using MediatR;
using Microsoft.AspNetCore.Mvc;
using Tinisoft.API.Controllers;
using Tinisoft.API.Attributes;
using Tinisoft.Application.Reviews.Commands.CreateReview;
using Tinisoft.Application.Reviews.Commands.UpdateReview;
using Tinisoft.Application.Reviews.Commands.DeleteReview;
using Tinisoft.Application.Reviews.Commands.ApproveReview;
using Tinisoft.Application.Reviews.Commands.ReplyToReview;
using Tinisoft.Application.Reviews.Commands.VoteReview;
using Tinisoft.Application.Reviews.Queries.GetProductReviews;

namespace Tinisoft.API.Controllers;

[ApiController]
[Route("api/reviews")]
public class ReviewsController : BaseController
{
    private readonly IMediator _mediator;
    private readonly ILogger<ReviewsController> _logger;

    public ReviewsController(IMediator mediator, ILogger<ReviewsController> logger)
    {
        _mediator = mediator;
        _logger = logger;
    }

    /// <summary>
    /// Ürün yorumlarını listele (Public)
    /// </summary>
    [HttpGet("product/{productId}")]
    [Public]
    public async Task<ActionResult<GetProductReviewsResponse>> GetProductReviews(
        Guid productId,
        [FromQuery] int page = 1,
        [FromQuery] int pageSize = 20,
        [FromQuery] string? sortBy = null,
        [FromQuery] string? sortOrder = null,
        [FromQuery] int? minRating = null,
        [FromQuery] int? maxRating = null,
        [FromQuery] bool? isVerifiedPurchase = null,
        [FromQuery] bool? hasReply = null,
        [FromQuery] bool? onlyWithImages = null)
    {
        var query = new GetProductReviewsQuery
        {
            ProductId = productId,
            Page = page,
            PageSize = pageSize,
            SortBy = sortBy,
            SortOrder = sortOrder,
            MinRating = minRating,
            MaxRating = maxRating,
            IsVerifiedPurchase = isVerifiedPurchase,
            HasReply = hasReply,
            OnlyWithImages = onlyWithImages
        };

        var result = await _mediator.Send(query);
        return Ok(result);
    }

    /// <summary>
    /// Yorum oluştur (Public - müşteriler yorum yapabilir)
    /// </summary>
    [HttpPost]
    [Public]
    public async Task<ActionResult<CreateReviewResponse>> CreateReview([FromBody] CreateReviewCommand command)
    {
        var result = await _mediator.Send(command);
        return CreatedAtAction(nameof(GetProductReviews), new { productId = command.ProductId }, result);
    }

    /// <summary>
    /// Yorum güncelle (Sadece yorum sahibi - CustomerId kontrolü yapılmalı)
    /// </summary>
    [HttpPut("{id}")]
    public async Task<ActionResult<UpdateReviewResponse>> UpdateReview(Guid id, [FromBody] UpdateReviewCommand command)
    {
        command.ReviewId = id;
        var result = await _mediator.Send(command);
        return Ok(result);
    }

    /// <summary>
    /// Yorum sil (Sadece yorum sahibi veya Admin - CustomerId kontrolü yapılmalı)
    /// </summary>
    [HttpDelete("{id}")]
    public async Task<ActionResult<DeleteReviewResponse>> DeleteReview(Guid id)
    {
        var command = new DeleteReviewCommand { ReviewId = id };
        var result = await _mediator.Send(command);
        return Ok(result);
    }

    /// <summary>
    /// Yorum oyla (Faydalı/Faydalı değil) - Public
    /// </summary>
    [HttpPost("{id}/vote")]
    [Public]
    public async Task<ActionResult<VoteReviewResponse>> VoteReview(Guid id, [FromBody] VoteReviewCommand command)
    {
        command.ReviewId = id;
        var result = await _mediator.Send(command);
        return Ok(result);
    }

    /// <summary>
    /// Yorum onayla/reddet (Admin/Moderator)
    /// </summary>
    [HttpPost("{id}/approve")]
    [RequireRole("Admin", "Moderator")]
    public async Task<ActionResult<ApproveReviewResponse>> ApproveReview(Guid id, [FromBody] ApproveReviewCommand command)
    {
        command.ReviewId = id;
        var result = await _mediator.Send(command);
        return Ok(result);
    }

    /// <summary>
    /// Yoruma yanıt ver (Mağaza sahibi/Admin)
    /// </summary>
    [HttpPost("{id}/reply")]
    [RequireRole("Admin", "Owner")]
    public async Task<ActionResult<ReplyToReviewResponse>> ReplyToReview(Guid id, [FromBody] ReplyToReviewCommand command)
    {
        command.ReviewId = id;
        var result = await _mediator.Send(command);
        return Ok(result);
    }
}

