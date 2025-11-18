using Tinisoft.Domain.Common;

namespace Tinisoft.Domain.Entities;

/// <summary>
/// Müşteri adresleri (shipping/billing)
/// </summary>
public class CustomerAddress : BaseEntity, ITenantEntity
{
    public Guid TenantId { get; set; }
    public Tenant? Tenant { get; set; }

    public Guid CustomerId { get; set; }
    public Customer? Customer { get; set; }

    public string AddressLine1 { get; set; } = string.Empty;
    public string? AddressLine2 { get; set; }
    public string City { get; set; } = string.Empty;
    public string? State { get; set; }
    public string PostalCode { get; set; } = string.Empty;
    public string Country { get; set; } = "TR";
    public string? Phone { get; set; }

    public bool IsDefaultShipping { get; set; }
    public bool IsDefaultBilling { get; set; }
    public string? AddressTitle { get; set; } // Ev, iş, vb.
}


