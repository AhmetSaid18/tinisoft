using FluentValidation;

namespace Tinisoft.Application.Invoices.Commands.CancelInvoice;

public class CancelInvoiceCommandValidator : AbstractValidator<CancelInvoiceCommand>
{
    public CancelInvoiceCommandValidator()
    {
        RuleFor(x => x.InvoiceId)
            .NotEmpty().WithMessage("Fatura ID gereklidir");

        RuleFor(x => x.CancellationReason)
            .NotEmpty().WithMessage("İptal nedeni gereklidir")
            .MaximumLength(500).WithMessage("İptal nedeni en fazla 500 karakter olabilir");
    }
}



