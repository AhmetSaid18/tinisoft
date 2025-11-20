using MediatR;

namespace Tinisoft.Application.Shipping.Queries.GetShippingProviders;

public class GetShippingProvidersQuery : IRequest<GetShippingProvidersResponse>
{
    public bool? IsActive { get; set; }
}

public class GetShippingProvidersResponse
{
    public List<ShippingProviderDto> Providers { get; set; } = new();
}

public class ShippingProviderDto
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



