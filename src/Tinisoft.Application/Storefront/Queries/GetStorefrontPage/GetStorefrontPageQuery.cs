using MediatR;

namespace Tinisoft.Application.Storefront.Queries.GetStorefrontPage;

public class GetStorefrontPageQuery : IRequest<GetStorefrontPageResponse?>
{
    public string Slug { get; set; } = string.Empty;
}

public class GetStorefrontPageResponse
{
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
    
    // Şablon
    public string Template { get; set; } = "default";
}

