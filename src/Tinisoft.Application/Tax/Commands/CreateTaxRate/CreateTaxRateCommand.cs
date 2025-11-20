using MediatR;

namespace Tinisoft.Application.Tax.Commands.CreateTaxRate;

public class CreateTaxRateCommand : IRequest<CreateTaxRateResponse>
{
    public string Name { get; set; } = string.Empty; // "KDV %20"
    public string Code { get; set; } = string.Empty; // "KDV20"
    public decimal Rate { get; set; } // 20.00 = %20
    public string Type { get; set; } = "VAT"; // VAT, SalesTax, ExciseTax
    public string? TaxCode { get; set; } // KDV kodu (001, 002, etc.) - E-Fatura için
    public string? ExciseTaxCode { get; set; } // ÖTV kodu (varsa)
    public string? ProductServiceCode { get; set; } // Mal/Hizmet kodu
    public bool IsIncludedInPrice { get; set; } = false; // Fiyata dahil mi?
    public string? EInvoiceTaxType { get; set; } // E-Fatura vergi tipi
    public bool IsExempt { get; set; } = false; // Vergiden muaf mı?
    public string? ExemptionReason { get; set; } // Muafiyet nedeni
    public string? Description { get; set; }
}

public class CreateTaxRateResponse
{
    public Guid TaxRateId { get; set; }
    public string Name { get; set; } = string.Empty;
}



