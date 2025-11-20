using MediatR;
using Tinisoft.Application.Shipping.Services;

namespace Tinisoft.Application.Shipping.Commands.CalculateShippingCost;

public class CalculateShippingCostCommand : IRequest<CalculateShippingCostResponse>
{
    public Guid? ShippingProviderId { get; set; } // Belirli bir provider için
    public string? ProviderCode { get; set; } // Veya provider code ile
    public string FromCity { get; set; } = string.Empty;
    public string ToCity { get; set; } = string.Empty;
    public decimal Weight { get; set; }
    public decimal? Width { get; set; }
    public decimal? Height { get; set; }
    public decimal? Depth { get; set; }
}

public class CalculateShippingCostResponse
{
    public decimal? ShippingCost { get; set; }
    public string Currency { get; set; } = "TRY";
    public string ProviderCode { get; set; } = string.Empty;
    public string ProviderName { get; set; } = string.Empty;
    public bool Success { get; set; }
    public string? ErrorMessage { get; set; }
}



