using MediatR;

namespace Tinisoft.Application.Shipping.Commands.UpdateShippingProvider;

public class UpdateShippingProviderCommand : IRequest<UpdateShippingProviderResponse>
{
    public Guid ShippingProviderId { get; set; }
    public string? ProviderName { get; set; }
    public string? ApiKey { get; set; }
    public string? ApiSecret { get; set; }
    public string? ApiUrl { get; set; }
    public string? TestApiUrl { get; set; }
    public bool? UseTestMode { get; set; }
    public string? SettingsJson { get; set; }
    public bool? IsDefault { get; set; }
    public int? Priority { get; set; }
    public bool? IsActive { get; set; }
}

public class UpdateShippingProviderResponse
{
    public Guid ShippingProviderId { get; set; }
    public string ProviderCode { get; set; } = string.Empty;
    public string ProviderName { get; set; } = string.Empty;
}



