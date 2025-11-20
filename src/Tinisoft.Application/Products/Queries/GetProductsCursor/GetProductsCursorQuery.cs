using MediatR;

namespace Tinisoft.Application.Products.Queries.GetProductsCursor;

/// <summary>
/// Cursor-based pagination - Shopify gibi büyük sistemlerde kullanılan yöntem
/// Offset-based pagination yerine cursor kullanır, milyarlarca ürün için optimize edilmiştir
/// </summary>
public class GetProductsCursorQuery : IRequest<GetProductsCursorResponse>
{
    public int Limit { get; set; } = 20; // Sayfa başına ürün sayısı (max 250)
    public string? Cursor { get; set; } // Son ürünün ID'si veya timestamp (base64 encoded)
    public string? Search { get; set; } // Meilisearch ile arama
    public Guid? CategoryId { get; set; }
    public bool? IsActive { get; set; }
    public string? SortBy { get; set; } // title, price, createdAt
    public string? SortOrder { get; set; } // asc, desc

    public int GetValidatedLimit()
    {
        // Shopify gibi: Maksimum 250 ürün per sayfa
        return Limit > 250 ? 250 : (Limit < 1 ? 20 : Limit);
    }
}

public class GetProductsCursorResponse
{
    public List<ProductListItemDto> Items { get; set; } = new();
    public string? NextCursor { get; set; } // Sonraki sayfa için cursor
    public string? PreviousCursor { get; set; } // Önceki sayfa için cursor
    public bool HasNextPage { get; set; }
    public bool HasPreviousPage { get; set; }
    public int Limit { get; set; }
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



