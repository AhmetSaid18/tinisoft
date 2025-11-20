using MediatR;

namespace Tinisoft.Application.Products.Queries.GetStorefrontCategories;

/// <summary>
/// Storefront için public kategori listesi
/// </summary>
public class GetStorefrontCategoriesQuery : IRequest<GetStorefrontCategoriesResponse>
{
}

public class GetStorefrontCategoriesResponse
{
    public List<StorefrontCategoryDto> Categories { get; set; } = new();
}

public class StorefrontCategoryDto
{
    public Guid Id { get; set; }
    public string Name { get; set; } = string.Empty;
    public string Slug { get; set; } = string.Empty;
    public string? Description { get; set; }
    public string? ImageUrl { get; set; }
    public Guid? ParentCategoryId { get; set; }
    public int DisplayOrder { get; set; }
    public List<StorefrontCategoryDto> SubCategories { get; set; } = new();
}



