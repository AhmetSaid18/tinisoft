using MediatR;

namespace Tinisoft.Application.Tenant.Commands.VerifyDomain;

public class VerifyDomainCommand : IRequest<VerifyDomainResponse>
{
    public Guid DomainId { get; set; }
}

public class VerifyDomainResponse
{
    public bool Success { get; set; }
    public string? Message { get; set; }
    public string? Host { get; set; }
    public string? Status { get; set; }  // pending_verification, verified, active
    public bool SslEnabled { get; set; }
}

