using MediatR;

namespace Tinisoft.Application.Payments.Commands.CreatePaymentProvider;

public class CreatePaymentProviderCommand : IRequest<CreatePaymentProviderResponse>
{
    public string ProviderCode { get; set; } = string.Empty; // "PAYTR", "KUVEYTTURK", "IYZICO", vb.
    public string ProviderName { get; set; } = string.Empty;
    public string? ApiKey { get; set; }
    public string? ApiSecret { get; set; }
    public string? ApiUrl { get; set; }
    public string? TestApiUrl { get; set; }
    public bool UseTestMode { get; set; } = false;
    public string? SettingsJson { get; set; } // JSON formatında: {"StoreId": "...", "CustomerId": "...", "Username": "...", "Password": "..."}
    public bool IsDefault { get; set; } = false;
    public int Priority { get; set; } = 0;
}

public class CreatePaymentProviderResponse
{
    public Guid PaymentProviderId { get; set; }
    public string ProviderCode { get; set; } = string.Empty;
    public string ProviderName { get; set; } = string.Empty;
}

