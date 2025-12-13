using MediatR;

namespace Tinisoft.Application.Pages.Commands.CreatePage;

public class CreatePageCommand : IRequest<CreatePageResponse>
{
    public string Title { get; set; } = string.Empty;
    public string Slug { get; set; } = string.Empty;
    public string Content { get; set; } = string.Empty;
    
    // SEO
    public string? MetaTitle { get; set; }
    public string? MetaDescription { get; set; }
    public string? MetaKeywords { get; set; }
    
    // Görsel
    public string? FeaturedImageUrl { get; set; }
    
    // Durum
    public bool IsPublished { get; set; } = false;
    
    // Şablon
    public string Template { get; set; } = "default";
    
    // Sıralama
    public int SortOrder { get; set; } = 0;
}

public class CreatePageResponse
{
    public Guid PageId { get; set; }
    public string Title { get; set; } = string.Empty;
    public string Slug { get; set; } = string.Empty;
    public string Message { get; set; } = "Sayfa başarıyla oluşturuldu.";
}

