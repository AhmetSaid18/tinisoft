using System.Text;
using Microsoft.Extensions.Logging;
using System.Xml.Linq;
using Microsoft.Extensions.Logging;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Caching.Distributed;
using Microsoft.Extensions.Logging;
using Tinisoft.Application.Common.Interfaces;
using Microsoft.Extensions.Logging;
using Tinisoft.Application.ProductFeeds.Services;
using Microsoft.Extensions.Logging;
using Tinisoft.Infrastructure.Persistence;
using Microsoft.Extensions.Logging;
using Finbuckle.MultiTenant;

using Microsoft.Extensions.Logging;
namespace Tinisoft.Infrastructure.Services;

public class ProductFeedService : IProductFeedService
{
    private readonly ApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly ICacheService _cacheService;
    private readonly ILogger<ProductFeedService> _logger;
    private const string CACHE_KEY_PREFIX = "feed:";

    public ProductFeedService(
        ApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor,
        ICacheService cacheService,
        ILogger<ProductFeedService> logger)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
        _cacheService = cacheService;
        _logger = logger;
    }

    public async Task<string> GenerateGoogleShoppingFeedAsync(CancellationToken cancellationToken = default)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);
        var cacheKey = $"{CACHE_KEY_PREFIX}google-shopping:{tenantId}";

        // Cache'den kontrol et
        var cachedFeed = await _cacheService.GetAsync<string>(cacheKey, cancellationToken);
        if (!string.IsNullOrEmpty(cachedFeed))
        {
            _logger.LogDebug("Google Shopping feed found in cache");
            return cachedFeed;
        }

        // Tenant bilgisi
        var tenant = await _dbContext.Tenants.FirstOrDefaultAsync(t => t.Id == tenantId, cancellationToken);
        if (tenant == null)
        {
            throw new InvalidOperationException("Tenant bulunamadı");
        }

        // Aktif ürünleri getir
        var products = await _dbContext.Products
            .Where(p => p.TenantId == tenantId && p.IsActive && p.Status == "Active")
            .Include(p => p.Images.OrderBy(i => i.Position).Take(1))
            .AsNoTracking()
            .ToListAsync(cancellationToken);

        // Google Shopping XML oluştur
        var xml = new XDocument(
            new XDeclaration("1.0", "UTF-8", null),
            new XElement("rss",
                new XAttribute("version", "2.0"),
                new XAttribute(XNamespace.Xmlns + "g", "http://base.google.com/ns/1.0"),
                new XElement("channel",
                    new XElement("title", tenant.SiteTitle ?? tenant.Name),
                    new XElement("link", $"https://{tenant.Slug}.tinisoft.com"),
                    new XElement("description", tenant.SiteDescription ?? ""),
                    products.Select(p =>
                    {
                        var item = new XElement("item",
                            new XElement("g:id", p.Id.ToString()),
                            new XElement("g:title", p.Title),
                            new XElement("g:description", p.ShortDescription ?? p.Description ?? ""),
                            new XElement("g:link", $"https://{tenant.Slug}.tinisoft.com/product/{p.Slug}"),
                            new XElement("g:image_link", p.Images.FirstOrDefault()?.OriginalUrl ?? ""),
                            new XElement("g:price", $"{p.Price} {p.Currency}"),
                            new XElement("g:availability", p.InventoryQuantity > 0 ? "in stock" : "out of stock"),
                            new XElement("g:condition", "new")
                        );
                        
                        if (!string.IsNullOrEmpty(p.Vendor))
                            item.Add(new XElement("g:brand", p.Vendor));
                        if (!string.IsNullOrEmpty(p.ProductType))
                            item.Add(new XElement("g:product_type", p.ProductType));
                        if (!string.IsNullOrEmpty(p.SKU))
                            item.Add(new XElement("g:mpn", p.SKU));
                        if (!string.IsNullOrEmpty(p.GTIN))
                            item.Add(new XElement("g:gtin", p.GTIN));
                            
                        return item;
                    })
                )
            )
        );

        var feedXml = xml.ToString();
        
        // Cache'e yaz (10 dakika)
        await _cacheService.SetAsync(cacheKey, feedXml, TimeSpan.FromMinutes(10), null, cancellationToken);

        _logger.LogInformation("Google Shopping feed generated: {ProductCount} products", products.Count);
        return feedXml;
    }

    public async Task<string> GenerateCimriFeedAsync(CancellationToken cancellationToken = default)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);
        var cacheKey = $"{CACHE_KEY_PREFIX}cimri:{tenantId}";

        // Cache'den kontrol et
        var cachedFeed = await _cacheService.GetAsync<string>(cacheKey, cancellationToken);
        if (!string.IsNullOrEmpty(cachedFeed))
        {
            _logger.LogDebug("Cimri feed found in cache");
            return cachedFeed;
        }

        // Tenant bilgisi
        var tenant = await _dbContext.Tenants.FirstOrDefaultAsync(t => t.Id == tenantId, cancellationToken);
        if (tenant == null)
        {
            throw new InvalidOperationException("Tenant bulunamadı");
        }

        // Aktif ürünleri getir
        var products = await _dbContext.Products
            .Where(p => p.TenantId == tenantId && p.IsActive && p.Status == "Active")
            .Include(p => p.Images.OrderBy(i => i.Position).Take(1))
            .AsNoTracking()
            .ToListAsync(cancellationToken);

        // Cimri XML oluştur
        var xml = new XDocument(
            new XDeclaration("1.0", "UTF-8", null),
            new XElement("products",
                products.Select(p => new XElement("product",
                    new XElement("name", p.Title),
                    new XElement("price", p.Price),
                    new XElement("currency", p.Currency),
                    new XElement("category", p.ProductType ?? ""),
                    new XElement("brand", p.Vendor ?? ""),
                    new XElement("image", p.Images.FirstOrDefault()?.OriginalUrl ?? ""),
                    new XElement("url", $"https://{tenant.Slug}.tinisoft.com/product/{p.Slug}"),
                    new XElement("description", p.ShortDescription ?? p.Description ?? ""),
                    !string.IsNullOrEmpty(p.SKU) ? new XElement("sku", p.SKU) : null,
                    new XElement("stock", p.InventoryQuantity > 0 ? "1" : "0")
                ))
            )
        );

        var feedXml = xml.ToString();
        
        // Cache'e yaz (10 dakika)
        await _cacheService.SetAsync(cacheKey, feedXml, TimeSpan.FromMinutes(10), null, cancellationToken);

        _logger.LogInformation("Cimri feed generated: {ProductCount} products", products.Count);
        return feedXml;
    }

    public async Task<string> GenerateCustomFeedAsync(string format, CancellationToken cancellationToken = default)
    {
        // Şimdilik Google Shopping formatını kullan
        return await GenerateGoogleShoppingFeedAsync();
    }
}

