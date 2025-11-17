using MediatR;

namespace Tinisoft.Application.Products.Queries.GetProducts;

public class GetProductsQuery : IRequest<GetProductsResponse>
{
    public int Page { get; set; } = 1;
    public int PageSize { get; set; } = 20;
    public string? Search { get; set; }
    public Guid? CategoryId { get; set; }
    public bool? IsActive { get; set; }
    public string? SortBy { get; set; } // title, price, createdAt
    public string? SortOrder { get; set; } // asc, desc

    // Validation - Max page size limit (performans için)
    public int GetValidatedPageSize()
    {
        // Maksimum 100 ürün per sayfa (performans için)
        return PageSize > 100 ? 100 : (PageSize < 1 ? 20 : PageSize);
    }
}

public class GetProductsResponse
{
    public List<ProductListItemDto> Items { get; set; } = new();
    public int TotalCount { get; set; }
    public int Page { get; set; }
    public int PageSize { get; set; }
    public int TotalPages => (int)Math.Ceiling(TotalCount / (double)PageSize);
}

public class ProductListItemDto
{
    public Guid Id { get; set; }
    public string Title { get; set; } = string.Empty;
    public string Slug { get; set; } = string.Empty;
    public string? SKU { get; set; }
    public decimal Price { get; set; }
    public decimal? CompareAtPrice { get; set; }
    public int? InventoryQuantity { get; set; }
    public bool IsActive { get; set; }
    public string? FeaturedImageUrl { get; set; }
    public DateTime CreatedAt { get; set; }
}

