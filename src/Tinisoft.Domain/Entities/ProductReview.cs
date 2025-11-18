using Tinisoft.Domain.Common;

namespace Tinisoft.Domain.Entities;

/// <summary>
/// Ürün yorumları ve puanlama sistemi
/// </summary>
public class ProductReview : BaseEntity, ITenantEntity
{
    public Guid TenantId { get; set; }
    public Tenant? Tenant { get; set; }
    
    public Guid ProductId { get; set; }
    public Product? Product { get; set; }
    
    // Müşteri (opsiyonel - anonymous review için null olabilir)
    public Guid? CustomerId { get; set; }
    public Customer? Customer { get; set; }
    
    // Anonymous reviewer bilgileri (CustomerId null ise)
    public string? ReviewerName { get; set; }
    public string? ReviewerEmail { get; set; }
    
    // Rating (1-5 yıldız)
    public int Rating { get; set; } // 1-5 arası
    
    // Review
    public string? Comment { get; set; } // Yorum metni
    public string? Title { get; set; } // Yorum başlığı (opsiyonel)
    
    // Moderation
    public bool IsApproved { get; set; } = false; // Onaylandı mı?
    public bool IsPublished { get; set; } = false; // Yayınlandı mı? (onaylandıktan sonra)
    public string? ModerationNote { get; set; } // Moderatör notu
    
    // Reply (mağaza sahibi yanıtı)
    public string? ReplyText { get; set; }
    public Guid? RepliedBy { get; set; } // User ID (mağaza sahibi/admin)
    public DateTime? RepliedAt { get; set; }
    
    // Helpful votes (beğenme/beğenmeme)
    public int HelpfulCount { get; set; } = 0; // Faydalı buldum
    public int NotHelpfulCount { get; set; } = 0; // Faydalı bulmadım
    
    // Order verification (gerçekten satın aldı mı?)
    public Guid? OrderId { get; set; } // Hangi siparişten?
    public Order? Order { get; set; }
    public bool IsVerifiedPurchase { get; set; } = false; // Doğrulanmış satın alma
    
    // Images (yorum fotoğrafları)
    public List<string> ImageUrls { get; set; } = new(); // Yorum fotoğrafları
    
    // Review type
    public string ReviewType { get; set; } = "Product"; // "Product", "Service", etc.
}

