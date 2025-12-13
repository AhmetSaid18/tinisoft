using MediatR;

namespace Tinisoft.Application.Pages.Commands.UpdatePage;

public class UpdatePageCommand : IRequest<UpdatePageResponse>
{
    public Guid PageId { get; set; }
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
    public bool IsPublished { get; set; }
    
    // Şablon
    public string Template { get; set; } = "default";
    
    // Sıralama
    public int SortOrder { get; set; }
}

public class UpdatePageResponse
{
    public Guid PageId { get; set; }
    public string Title { get; set; } = string.Empty;
    public string Slug { get; set; } = string.Empty;
    public string Message { get; set; } = "Sayfa başarıyla güncellendi.";
}

