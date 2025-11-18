namespace Tinisoft.Application.ProductFeeds.Services;

/// <summary>
/// Product feed service - XML feed'leri oluşturur (Google Shopping, Cimri, etc.)
/// </summary>
public interface IProductFeedService
{
    /// <summary>
    /// Google Shopping XML feed oluşturur
    /// </summary>
    Task<string> GenerateGoogleShoppingFeedAsync(CancellationToken cancellationToken = default);

    /// <summary>
    /// Cimri XML feed oluşturur
    /// </summary>
    Task<string> GenerateCimriFeedAsync(CancellationToken cancellationToken = default);

    /// <summary>
    /// Custom XML feed oluşturur
    /// </summary>
    Task<string> GenerateCustomFeedAsync(string format, CancellationToken cancellationToken = default);
}

