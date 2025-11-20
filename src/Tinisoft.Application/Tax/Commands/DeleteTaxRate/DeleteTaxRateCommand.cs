using MediatR;

namespace Tinisoft.Application.Tax.Commands.DeleteTaxRate;

public class DeleteTaxRateCommand : IRequest<Unit>
{
    public Guid TaxRateId { get; set; }
}



