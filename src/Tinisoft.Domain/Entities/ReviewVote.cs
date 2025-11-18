using Tinisoft.Domain.Common;

namespace Tinisoft.Domain.Entities;

/// <summary>
/// Yorum beğeni/beğenmeme oyları (duplicate vote önlemek için)
/// </summary>
public class ReviewVote : BaseEntity
{
    public Guid TenantId { get; set; }
    public Tenant? Tenant { get; set; }
    
    public Guid ReviewId { get; set; }
    public ProductReview? Review { get; set; }
    
    // Müşteri (opsiyonel - anonymous vote için null)
    public Guid? CustomerId { get; set; }
    public Customer? Customer { get; set; }
    
    // Anonymous vote için IP adresi
    public string? IpAddress { get; set; }
    
    // Vote type
    public bool IsHelpful { get; set; } = true; // true = faydalı, false = faydalı değil
}

