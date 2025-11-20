using MediatR;

namespace Tinisoft.Application.Resellers.Commands.CreateResellerPrice;

public class CreateResellerPriceCommand : IRequest<CreateResellerPriceResponse>
{
    public Guid ResellerId { get; set; }
    public Guid ProductId { get; set; }
    
    // Pricing
    public decimal Price { get; set; }
    public decimal? CompareAtPrice { get; set; }
    public string Currency { get; set; } = "TRY";
    
    // Quantity Break Pricing
    public int? MinQuantity { get; set; }
    public int? MaxQuantity { get; set; }
    
    // Validity
    public DateTime? ValidFrom { get; set; }
    public DateTime? ValidUntil { get; set; }
    
    // Notes
    public string? Notes { get; set; }
}

public class CreateResellerPriceResponse
{
    public Guid ResellerPriceId { get; set; }
    public Guid ResellerId { get; set; }
    public Guid ProductId { get; set; }
    public decimal Price { get; set; }
}



