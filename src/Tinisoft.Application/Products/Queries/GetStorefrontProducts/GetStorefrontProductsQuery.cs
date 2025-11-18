using MediatR;

namespace Tinisoft.Application.Products.Queries.GetStorefrontProducts;

/// <summary>
/// Storefront için public ürün listesi (müşteriler için - tenant'ın seçtiği kura göre fiyat gösterimi)
/// </summary>
public class GetStorefrontProductsQuery : IRequest<GetStorefrontProductsResponse>
{
    public int Page { get; set; } = 1;
    public int PageSize { get; set; } = 20;
    public string? Search { get; set; }
    public Guid? CategoryId { get; set; }
    public string? SortBy { get; set; } // title, price, createdAt
    public string? SortOrder { get; set; } // asc, desc
    public string? PreferredCurrency { get; set; } // Müşterinin tercih ettiği para birimi (opsiyonel)

    public int GetValidatedPageSize()
    {
        return PageSize > 100 ? 100 : (PageSize < 1 ? 20 : PageSize);
    }
}

public class GetStorefrontProductsResponse
{
    public List<StorefrontProductDto> Items { get; set; } = new();
    public int TotalCount { get; set; }
    public int Page { get; set; }
    public int PageSize { get; set; }
    public int TotalPages => (int)Math.Ceiling(TotalCount / (double)PageSize);
    public string DisplayCurrency { get; set; } = "TRY"; // Gösterilen para birimi
}

public class StorefrontProductDto
{
    public Guid Id { get; set; }
    public string Title { get; set; } = string.Empty;
    public string Slug { get; set; } = string.Empty;
    public string? ShortDescription { get; set; }
    public string? SKU { get; set; }
    public decimal Price { get; set; } // Tenant'ın seçtiği kura göre dönüştürülmüş fiyat
    public decimal? CompareAtPrice { get; set; }
    public string Currency { get; set; } = "TRY"; // Gösterilen para birimi
    public int? InventoryQuantity { get; set; }
    public bool IsInStock => InventoryQuantity == null || InventoryQuantity > 0;
    public string? FeaturedImageUrl { get; set; }
    public List<string> Categories { get; set; } = new();
    public DateTime CreatedAt { get; set; }
}

