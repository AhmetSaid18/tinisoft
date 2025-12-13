using MediatR;

namespace Tinisoft.Application.Tenant.Commands.AddCustomDomain;

public class AddCustomDomainCommand : IRequest<AddCustomDomainResponse>
{
    public string Host { get; set; } = string.Empty;  // www.ornekmagaza.com
    public bool IsPrimary { get; set; } = false;
}

public class AddCustomDomainResponse
{
    public Guid DomainId { get; set; }
    public string Host { get; set; } = string.Empty;
    public string Status { get; set; } = string.Empty;  // pending_verification, verified, active
    public string VerificationToken { get; set; } = string.Empty;
    public DnsInstructions? Instructions { get; set; }
    public bool Success { get; set; }
    public string? ErrorMessage { get; set; }
}

public class DnsInstructions
{
    public TxtRecordInstruction TxtRecord { get; set; } = new();
    public CnameRecordInstruction CnameRecord { get; set; } = new();
}

public class TxtRecordInstruction
{
    public string Type { get; set; } = "TXT";
    public string Name { get; set; } = "_tinisoft-verification";
    public string Value { get; set; } = string.Empty;
    public int Ttl { get; set; } = 3600;
}

public class CnameRecordInstruction
{
    public string Type { get; set; } = "CNAME";
    public string Name { get; set; } = "www";
    public string Value { get; set; } = string.Empty;  // ornek-magaza.domains.tinisoft.com
    public int Ttl { get; set; } = 3600;
}

