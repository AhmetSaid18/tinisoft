using FluentValidation;

namespace Tinisoft.Application.Invoices.Commands.CreateInvoice;

public class CreateInvoiceCommandValidator : AbstractValidator<CreateInvoiceCommand>
{
    public CreateInvoiceCommandValidator()
    {
        RuleFor(x => x.OrderId)
            .NotEmpty().WithMessage("Sipariş ID gereklidir");

        RuleFor(x => x.InvoiceType)
            .Must(x => x == null || x == "eFatura" || x == "EArsiv")
            .WithMessage("Fatura tipi 'eFatura' veya 'EArsiv' olmalıdır");

        RuleFor(x => x.ProfileId)
            .Must(x => x == null || x == "TICARIFATURA" || x == "EARSIVFATURA" || x == "TEMELFATURA")
            .WithMessage("Profil ID geçersiz");
    }
}



