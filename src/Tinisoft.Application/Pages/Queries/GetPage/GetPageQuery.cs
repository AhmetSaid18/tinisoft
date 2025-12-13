using MediatR;

namespace Tinisoft.Application.Pages.Queries.GetPage;

public class GetPageQuery : IRequest<GetPageResponse>
{
    public Guid? PageId { get; set; }
    public string? Slug { get; set; }
}

public class GetPageResponse
{
    public Guid Id { get; set; }
    public string Title { get; set; } = string.Empty;
    public string Slug { get; set; } = string.Empty;
    public string Content { get; set; } = string.Empty;
    
    // SEO
    public string? MetaTitle { get; set; }
    public string? MetaDescription { get; set; }
    public string? MetaKeywords { get; set; }
    public string? CanonicalUrl { get; set; }
    
    // Görsel
    public string? FeaturedImageUrl { get; set; }
    
    // Durum
    public bool IsPublished { get; set; }
    public DateTime? PublishedAt { get; set; }
    
    // Şablon
    public string Template { get; set; } = "default";
    
    // Sıralama
    public int SortOrder { get; set; }
    
    // Sistem
    public bool IsSystemPage { get; set; }
    public string? SystemPageType { get; set; }
    
    // Tarihler
    public DateTime CreatedAt { get; set; }
    public DateTime? UpdatedAt { get; set; }
}

