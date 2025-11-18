using MediatR;

namespace Tinisoft.Application.Reviews.Commands.CreateReview;

public class CreateReviewCommand : IRequest<CreateReviewResponse>
{
    public Guid ProductId { get; set; }
    
    // Müşteri bilgileri (opsiyonel - anonymous review için)
    public Guid? CustomerId { get; set; }
    public string? ReviewerName { get; set; } // CustomerId null ise gerekli
    public string? ReviewerEmail { get; set; } // CustomerId null ise gerekli
    
    // Rating (1-5 yıldız)
    public int Rating { get; set; } // 1-5 arası (validation gerekli)
    
    // Review
    public string? Comment { get; set; }
    public string? Title { get; set; } // Opsiyonel başlık
    
    // Order verification (gerçekten satın aldı mı?)
    public Guid? OrderId { get; set; }
    
    // Images
    public List<string> ImageUrls { get; set; } = new();
}

public class CreateReviewResponse
{
    public Guid ReviewId { get; set; }
    public bool IsApproved { get; set; } // Otomatik onaylanırsa true, değilse moderasyon gerekiyor
    public string Message { get; set; } = string.Empty;
}

