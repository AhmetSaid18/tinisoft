using FluentValidation;

namespace Tinisoft.Application.Reviews.Commands.CreateReview;

public class CreateReviewCommandValidator : AbstractValidator<CreateReviewCommand>
{
    public CreateReviewCommandValidator()
    {
        RuleFor(x => x.ProductId)
            .NotEmpty().WithMessage("Ürün ID gereklidir");

        RuleFor(x => x.Rating)
            .InclusiveBetween(1, 5).WithMessage("Rating 1-5 arası olmalıdır");

        RuleFor(x => x.Comment)
            .MaximumLength(5000).WithMessage("Yorum en fazla 5000 karakter olabilir");

        RuleFor(x => x.Title)
            .MaximumLength(200).WithMessage("Başlık en fazla 200 karakter olabilir");

        // Anonymous review için name ve email gerekli
        RuleFor(x => x.ReviewerName)
            .NotEmpty().When(x => !x.CustomerId.HasValue)
            .WithMessage("Müşteri adı gereklidir");

        RuleFor(x => x.ReviewerEmail)
            .NotEmpty().When(x => !x.CustomerId.HasValue)
            .EmailAddress().When(x => !x.CustomerId.HasValue)
            .WithMessage("Geçerli bir email adresi gereklidir");

        // Image URL'leri kontrolü
        RuleForEach(x => x.ImageUrls)
            .Must(url => Uri.TryCreate(url, UriKind.Absolute, out _))
            .When(x => x.ImageUrls.Any())
            .WithMessage("Geçersiz image URL formatı");
    }
}



