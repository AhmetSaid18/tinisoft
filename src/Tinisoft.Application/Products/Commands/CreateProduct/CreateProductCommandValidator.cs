using FluentValidation;

namespace Tinisoft.Application.Products.Commands.CreateProduct;

public class CreateProductCommandValidator : AbstractValidator<CreateProductCommand>
{
    public CreateProductCommandValidator()
    {
        RuleFor(x => x.Title)
            .NotEmpty().WithMessage("Ürün başlığı gereklidir")
            .MaximumLength(200).WithMessage("Ürün başlığı en fazla 200 karakter olabilir");

        RuleFor(x => x.Slug)
            .NotEmpty().WithMessage("Slug gereklidir")
            .Matches(@"^[a-z0-9]+(?:-[a-z0-9]+)*$").WithMessage("Geçersiz slug formatı");

        RuleFor(x => x.Price)
            .GreaterThanOrEqualTo(0).WithMessage("Fiyat 0'dan küçük olamaz");

        RuleFor(x => x.CompareAtPrice)
            .GreaterThan(x => x.Price).When(x => x.CompareAtPrice.HasValue)
            .WithMessage("Karşılaştırma fiyatı, normal fiyattan büyük olmalıdır");

        RuleFor(x => x.CostPerItem)
            .GreaterThanOrEqualTo(0).WithMessage("Maliyet 0'dan küçük olamaz");

        RuleFor(x => x.InventoryQuantity)
            .GreaterThanOrEqualTo(0).When(x => x.TrackInventory)
            .WithMessage("Stok miktarı 0'dan küçük olamaz");
    }
}



