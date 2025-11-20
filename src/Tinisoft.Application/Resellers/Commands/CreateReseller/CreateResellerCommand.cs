using MediatR;

namespace Tinisoft.Application.Resellers.Commands.CreateReseller;

public class CreateResellerCommand : IRequest<CreateResellerResponse>
{
    // Basic Info
    public string CompanyName { get; set; } = string.Empty;
    public string? TaxNumber { get; set; }
    public string? TaxOffice { get; set; }
    
    // Contact Info
    public string Email { get; set; } = string.Empty;
    public string? Phone { get; set; }
    public string? Mobile { get; set; }
    
    // Address
    public string? Address { get; set; }
    public string? City { get; set; }
    public string? State { get; set; }
    public string? PostalCode { get; set; }
    public string? Country { get; set; }
    
    // Contact Person
    public string? ContactPersonName { get; set; }
    public string? ContactPersonTitle { get; set; }
    
    // Credit & Payment
    public decimal CreditLimit { get; set; } = 0;
    public int PaymentTermDays { get; set; } = 30;
    public string PaymentMethod { get; set; } = "Invoice";
    
    // Pricing
    public decimal DefaultDiscountPercent { get; set; } = 0;
    public bool UseCustomPricing { get; set; } = false;
    
    // Notes
    public string? Notes { get; set; }
}

public class CreateResellerResponse
{
    public Guid ResellerId { get; set; }
    public string CompanyName { get; set; } = string.Empty;
    public string Email { get; set; } = string.Empty;
}



