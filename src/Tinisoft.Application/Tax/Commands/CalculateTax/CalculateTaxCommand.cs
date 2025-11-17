using MediatR;

namespace Tinisoft.Application.Tax.Commands.CalculateTax;

public class CalculateTaxCommand : IRequest<CalculateTaxResponse>
{
    public Guid? ProductId { get; set; }
    public Guid? CategoryId { get; set; }
    public string? ProductType { get; set; }
    public decimal Price { get; set; } // Vergi hesaplanacak fiyat
    public int Quantity { get; set; } = 1;
    public string? CountryCode { get; set; } = "TR"; // Varsayılan Türkiye
    public string? Region { get; set; }
    public Guid? TaxRateId { get; set; } // Manuel vergi oranı seçilmişse
}

public class CalculateTaxResponse
{
    public decimal Subtotal { get; set; } // Vergi öncesi toplam
    public decimal TaxAmount { get; set; } // Vergi tutarı
    public decimal Total { get; set; } // Vergi dahil toplam
    public List<TaxDetailDto> TaxDetails { get; set; } = new(); // Detaylı vergi bilgileri
}

public class TaxDetailDto
{
    public Guid TaxRateId { get; set; }
    public string TaxName { get; set; } = string.Empty;
    public string TaxCode { get; set; } = string.Empty;
    public decimal Rate { get; set; } // %20 = 20.00
    public decimal TaxableAmount { get; set; } // Vergiye tabi tutar
    public decimal TaxAmount { get; set; } // Bu vergiden gelen tutar
    public string Type { get; set; } = string.Empty; // VAT, SalesTax, etc.
}

