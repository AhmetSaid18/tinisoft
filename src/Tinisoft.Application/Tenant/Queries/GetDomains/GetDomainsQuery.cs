using MediatR;

namespace Tinisoft.Application.Tenant.Queries.GetDomains;

public class GetDomainsQuery : IRequest<GetDomainsResponse>
{
}

public class GetDomainsResponse
{
    public List<DomainDto> Domains { get; set; } = new();
}

public class DomainDto
{
    public Guid Id { get; set; }
    public string Host { get; set; } = string.Empty;
    public bool IsPrimary { get; set; }
    public bool IsVerified { get; set; }
    public string Status { get; set; } = string.Empty;
    public bool SslEnabled { get; set; }
    public DateTime? SslExpiresAt { get; set; }
    public DateTime CreatedAt { get; set; }
    public DateTime? VerifiedAt { get; set; }
}

