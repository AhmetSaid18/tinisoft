using Tinisoft.Domain.Common;

namespace Tinisoft.Domain.Entities;

public class Domain : BaseEntity
{
    public Guid TenantId { get; set; }
    public Tenant? Tenant { get; set; }
    
    public string Host { get; set; } = string.Empty; // www.marka.com veya marka.com
    public bool IsPrimary { get; set; }
    public bool IsVerified { get; set; }
    public string? VerificationToken { get; set; }
    public DateTime? VerifiedAt { get; set; }
    
    // SSL/TLS
    public bool SslEnabled { get; set; }
    public DateTime? SslIssuedAt { get; set; }
    public DateTime? SslExpiresAt { get; set; }
}

