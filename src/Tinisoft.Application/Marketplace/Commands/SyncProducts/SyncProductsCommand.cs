using MediatR;

namespace Tinisoft.Application.Marketplace.Commands.SyncProducts;

public class SyncProductsCommand : IRequest<SyncProductsResponse>
{
    public string Marketplace { get; set; } = string.Empty; // Trendyol, Hepsiburada, N11
    public List<Guid>? ProductIds { get; set; } // Belirli ürünler, null ise tümü
}

public class SyncProductsResponse
{
    public int SyncedCount { get; set; }
    public int FailedCount { get; set; }
    public List<string> Errors { get; set; } = new();
}

