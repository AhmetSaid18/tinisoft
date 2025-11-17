using MediatR;

namespace Tinisoft.Application.Tax.Commands.UpdateTaxRate;

public class UpdateTaxRateCommand : IRequest<UpdateTaxRateResponse>
{
    public Guid TaxRateId { get; set; }
    public string Name { get; set; } = string.Empty;
    public string Code { get; set; } = string.Empty;
    public decimal Rate { get; set; }
    public string Type { get; set; } = "VAT";
    public string? TaxCode { get; set; }
    public string? ExciseTaxCode { get; set; }
    public string? ProductServiceCode { get; set; }
    public bool IsIncludedInPrice { get; set; }
    public string? EInvoiceTaxType { get; set; }
    public bool IsExempt { get; set; }
    public string? ExemptionReason { get; set; }
    public bool IsActive { get; set; }
    public string? Description { get; set; }
}

public class UpdateTaxRateResponse
{
    public Guid TaxRateId { get; set; }
    public string Name { get; set; } = string.Empty;
}

