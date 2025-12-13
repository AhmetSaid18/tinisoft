using MediatR;

namespace Tinisoft.Application.Tenant.Commands.RemoveDomain;

public class RemoveDomainCommand : IRequest<RemoveDomainResponse>
{
    public Guid DomainId { get; set; }
}

public class RemoveDomainResponse
{
    public bool Success { get; set; }
    public string? Message { get; set; }
}

