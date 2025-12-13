using MediatR;

namespace Tinisoft.Application.Payments.Queries.GetPaymentProviders;

public class GetPaymentProvidersQuery : IRequest<GetPaymentProvidersResponse>
{
    public bool? IsActive { get; set; }
}

public class GetPaymentProvidersResponse
{
    public List<PaymentProviderDto> Providers { get; set; } = new();
}

public class PaymentProviderDto
{
    public Guid Id { get; set; }
    public string ProviderCode { get; set; } = string.Empty;
    public string ProviderName { get; set; } = string.Empty;
    public bool IsActive { get; set; }
    public bool IsDefault { get; set; }
    public int Priority { get; set; }
    public bool UseTestMode { get; set; }
    public bool HasApiKey { get; set; } // API key var mı? (güvenlik için key'i göstermiyoruz)
}

