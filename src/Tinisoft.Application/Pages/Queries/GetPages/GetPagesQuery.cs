using MediatR;

namespace Tinisoft.Application.Pages.Queries.GetPages;

public class GetPagesQuery : IRequest<GetPagesResponse>
{
    public bool? IsPublished { get; set; }
    public string? SearchTerm { get; set; }
    public int Page { get; set; } = 1;
    public int PageSize { get; set; } = 20;
}

public class GetPagesResponse
{
    public List<PageDto> Pages { get; set; } = new();
    public int TotalCount { get; set; }
    public int Page { get; set; }
    public int PageSize { get; set; }
    public int TotalPages { get; set; }
}

public class PageDto
{
    public Guid Id { get; set; }
    public string Title { get; set; } = string.Empty;
    public string Slug { get; set; } = string.Empty;
    public string? MetaTitle { get; set; }
    public string? MetaDescription { get; set; }
    public string? FeaturedImageUrl { get; set; }
    public bool IsPublished { get; set; }
    public DateTime? PublishedAt { get; set; }
    public string Template { get; set; } = "default";
    public int SortOrder { get; set; }
    public bool IsSystemPage { get; set; }
    public string? SystemPageType { get; set; }
    public DateTime CreatedAt { get; set; }
    public DateTime? UpdatedAt { get; set; }
}

