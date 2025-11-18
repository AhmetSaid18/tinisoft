using MediatR;

namespace Tinisoft.Application.Shipping.Commands.CreateShippingProvider;

public class CreateShippingProviderCommand : IRequest<CreateShippingProviderResponse>
{
    public string ProviderCode { get; set; } = string.Empty; // "ARAS", "MNG", "YURTICI", vb.
    public string ProviderName { get; set; } = string.Empty;
    public string? ApiKey { get; set; }
    public string? ApiSecret { get; set; }
    public string? ApiUrl { get; set; }
    public string? TestApiUrl { get; set; }
    public bool UseTestMode { get; set; } = false;
    public string? SettingsJson { get; set; }
    public bool IsDefault { get; set; } = false;
    public int Priority { get; set; } = 0;
}

public class CreateShippingProviderResponse
{
    public Guid ShippingProviderId { get; set; }
    public string ProviderCode { get; set; } = string.Empty;
    public string ProviderName { get; set; } = string.Empty;
}

