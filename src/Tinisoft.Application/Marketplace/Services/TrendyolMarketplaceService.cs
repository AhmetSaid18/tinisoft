using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;
using Microsoft.Extensions.Configuration;
using Tinisoft.Domain.Entities;

namespace Tinisoft.Application.Marketplace.Services;

public class TrendyolMarketplaceService : IMarketplaceService
{
    private readonly ILogger<TrendyolMarketplaceService> _logger;
    private readonly HttpClient _httpClient;
    private readonly IConfiguration _configuration;
    private readonly IApplicationDbContext _dbContext;

    public TrendyolMarketplaceService(
        ILogger<TrendyolMarketplaceService> logger,
        HttpClient httpClient,
        IConfiguration configuration,
        IApplicationDbContext dbContext)
    {
        _logger = logger;
        _httpClient = httpClient;
        _configuration = configuration;
        _dbContext = dbContext;
    }

    public async Task<SyncProductsResponse> SyncProductsAsync(MarketplaceIntegration integration, List<Guid>? productIds, CancellationToken cancellationToken)
    {
        _logger.LogInformation("Syncing products to Trendyol for integration {IntegrationId}", integration.Id);
        
        var response = new SyncProductsResponse();
        
        try
        {
            // Trendyol API credentials
            var apiUrl = _configuration["Marketplace:Trendyol:ApiUrl"] ?? "https://api.trendyol.com/sapigw";
            var supplierId = integration.SupplierId ?? _configuration["Marketplace:Trendyol:SupplierId"];
            var apiKey = integration.ApiKey ?? _configuration["Marketplace:Trendyol:ApiKey"];
            var apiSecret = integration.ApiSecret ?? _configuration["Marketplace:Trendyol:ApiSecret"];

            if (string.IsNullOrEmpty(apiKey) || string.IsNullOrEmpty(apiSecret))
            {
                _logger.LogError("Trendyol API credentials are missing");
                response.FailedCount = productIds?.Count ?? 0;
                response.Errors.Add("Trendyol API credentials are missing");
                return response;
            }

            // Get products from database
            var products = productIds != null
                ? await _dbContext.Products
                    .Where(p => productIds.Contains(p.Id) && p.TenantId == integration.TenantId)
                    .ToListAsync(cancellationToken)
                : await _dbContext.Products
                    .Where(p => p.TenantId == integration.TenantId && p.IsActive)
                    .Take(100) // Limit to 100 products per sync
                    .ToListAsync(cancellationToken);

            // Configure HttpClient
            _httpClient.DefaultRequestHeaders.Clear();
            _httpClient.DefaultRequestHeaders.Add("User-Agent", $"{supplierId} - SelfIntegration");
            
            // Basic authentication
            var authString = $"{apiKey}:{apiSecret}";
            var base64Auth = Convert.ToBase64String(Encoding.UTF8.GetBytes(authString));
            _httpClient.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Basic", base64Auth);

            // Sync each product
            foreach (var product in products)
            {
                try
                {
                    // Prepare Trendyol product model
                    var trendyolProduct = new
                    {
                        barcode = product.Barcode ?? product.SKU ?? product.Id.ToString(),
                        title = product.Title,
                        productMainId = product.Id.ToString(),
                        brandId = 0, // Should be mapped from Trendyol brand list
                        categoryId = 0, // Should be mapped from Trendyol category list
                        quantity = product.InventoryQuantity ?? 0,
                        stockCode = product.SKU,
                        dimensionalWeight = 0,
                        description = product.Description ?? product.ShortDescription ?? "",
                        currencyType = "TRY",
                        listPrice = product.Price,
                        salePrice = product.CompareAtPrice ?? product.Price,
                        vatRate = 18,
                        cargoCompanyId = 10, // Default cargo company
                        images = new[]
                        {
                            new { url = product.Images?.FirstOrDefault()?.OriginalUrl ?? "" }
                        },
                        attributes = new[]
                        {
                            new { attributeId = 0, attributeValueId = 0 }
                        }
                    };

                    var json = JsonSerializer.Serialize(trendyolProduct);
                    var content = new StringContent(json, Encoding.UTF8, "application/json");

                    // POST to Trendyol API
                    var apiResponse = await _httpClient.PostAsync(
                        $"{apiUrl}/suppliers/{supplierId}/v2/products",
                        content,
                        cancellationToken);

                    if (apiResponse.IsSuccessStatusCode)
                    {
                        response.SyncedCount++;
                        _logger.LogInformation("Product {ProductId} synced successfully to Trendyol", product.Id);
                    }
                    else
                    {
                        var errorContent = await apiResponse.Content.ReadAsStringAsync(cancellationToken);
                        response.FailedCount++;
                        response.Errors.Add($"Product {product.Title}: {errorContent}");
                        _logger.LogWarning("Failed to sync product {ProductId}: {Error}", product.Id, errorContent);
                    }
                }
                catch (Exception ex)
                {
                    response.FailedCount++;
                    response.Errors.Add($"Product {product.Title}: {ex.Message}");
                    _logger.LogError(ex, "Error syncing product {ProductId}", product.Id);
                }
            }
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error syncing products to Trendyol");
            response.Errors.Add($"General error: {ex.Message}");
        }
        
        return response;
    }

    public async Task<SyncOrdersResponse> SyncOrdersAsync(MarketplaceIntegration integration, CancellationToken cancellationToken)
    {
        _logger.LogInformation("Syncing orders from Trendyol for integration {IntegrationId}", integration.Id);
        
        var response = new SyncOrdersResponse();
        
        try
        {
            // Trendyol API credentials
            var apiUrl = _configuration["Marketplace:Trendyol:ApiUrl"] ?? "https://api.trendyol.com/sapigw";
            var supplierId = integration.SupplierId ?? _configuration["Marketplace:Trendyol:SupplierId"];
            var apiKey = integration.ApiKey ?? _configuration["Marketplace:Trendyol:ApiKey"];
            var apiSecret = integration.ApiSecret ?? _configuration["Marketplace:Trendyol:ApiSecret"];

            if (string.IsNullOrEmpty(apiKey) || string.IsNullOrEmpty(apiSecret))
            {
                _logger.LogError("Trendyol API credentials are missing");
                response.Errors.Add("Trendyol API credentials are missing");
                return response;
            }

            // Configure HttpClient
            _httpClient.DefaultRequestHeaders.Clear();
            _httpClient.DefaultRequestHeaders.Add("User-Agent", $"{supplierId} - SelfIntegration");
            
            var authString = $"{apiKey}:{apiSecret}";
            var base64Auth = Convert.ToBase64String(Encoding.UTF8.GetBytes(authString));
            _httpClient.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Basic", base64Auth);

            // Get orders from Trendyol (last 7 days)
            var startDate = DateTime.UtcNow.AddDays(-7).ToString("yyyy-MM-dd");
            var endDate = DateTime.UtcNow.ToString("yyyy-MM-dd");
            
            var apiResponse = await _httpClient.GetAsync(
                $"{apiUrl}/suppliers/{supplierId}/orders?startDate={startDate}&endDate={endDate}&page=0&size=50",
                cancellationToken);

            if (apiResponse.IsSuccessStatusCode)
            {
                var jsonResponse = await apiResponse.Content.ReadAsStringAsync(cancellationToken);
                var ordersData = JsonSerializer.Deserialize<TrendyolOrdersResponse>(jsonResponse);

                if (ordersData?.Content != null)
                {
                    foreach (var trendyolOrder in ordersData.Content)
                    {
                        try
                        {
                            // Check if order already exists
                            var existingOrder = await _dbContext.Orders
                                .FirstOrDefaultAsync(o => 
                                    o.TenantId == integration.TenantId && 
                                    o.OrderNumber == trendyolOrder.OrderNumber,
                                    cancellationToken);

                            if (existingOrder == null)
                            {
                                // Create new order
                                var newOrder = new Order
                                {
                                    TenantId = integration.TenantId,
                                    OrderNumber = trendyolOrder.OrderNumber,
                                    Status = MapTrendyolStatus(trendyolOrder.Status),
                                    CustomerEmail = trendyolOrder.CustomerEmail ?? "trendyol@marketplace.com",
                                    CustomerFirstName = trendyolOrder.CustomerFirstName,
                                    CustomerLastName = trendyolOrder.CustomerLastName,
                                    ShippingAddressLine1 = trendyolOrder.ShipmentAddress?.Address,
                                    ShippingCity = trendyolOrder.ShipmentAddress?.City,
                                    ShippingState = trendyolOrder.ShipmentAddress?.District,
                                    ShippingPostalCode = trendyolOrder.ShipmentAddress?.PostalCode,
                                    ShippingCountry = "TR",
                                    TotalsJson = JsonSerializer.Serialize(new
                                    {
                                        subtotal = trendyolOrder.GrossAmount,
                                        tax = 0,
                                        shipping = 0,
                                        discount = 0,
                                        total = trendyolOrder.GrossAmount
                                    }),
                                    PaymentStatus = "Paid", // Trendyol orders are pre-paid
                                    CreatedAt = trendyolOrder.OrderDate
                                };

                                _dbContext.Orders.Add(newOrder);
                                response.SyncedCount++;
                                _logger.LogInformation("Order {OrderNumber} synced from Trendyol", trendyolOrder.OrderNumber);
                            }
                        }
                        catch (Exception ex)
                        {
                            response.FailedCount++;
                            response.Errors.Add($"Order {trendyolOrder.OrderNumber}: {ex.Message}");
                            _logger.LogError(ex, "Error syncing order {OrderNumber}", trendyolOrder.OrderNumber);
                        }
                    }

                    await _dbContext.SaveChangesAsync(cancellationToken);
                }
            }
            else
            {
                var errorContent = await apiResponse.Content.ReadAsStringAsync(cancellationToken);
                response.Errors.Add($"API Error: {errorContent}");
                _logger.LogWarning("Failed to get orders from Trendyol: {Error}", errorContent);
            }
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error syncing orders from Trendyol");
            response.Errors.Add($"General error: {ex.Message}");
        }
        
        return response;
    }

    private string MapTrendyolStatus(string trendyolStatus)
    {
        return trendyolStatus?.ToLower() switch
        {
            "created" => "Pending",
            "picking" => "Processing",
            "invoiced" => "Processing",
            "shipped" => "Shipped",
            "delivered" => "Delivered",
            "cancelled" => "Cancelled",
            _ => "Pending"
        };
    }
}

// Trendyol API response models
public class TrendyolOrdersResponse
{
    public List<TrendyolOrder>? Content { get; set; }
    public int TotalPages { get; set; }
    public int TotalElements { get; set; }
}

public class TrendyolOrder
{
    public string OrderNumber { get; set; } = string.Empty;
    public string? Status { get; set; }
    public decimal GrossAmount { get; set; }
    public string? CustomerEmail { get; set; }
    public string? CustomerFirstName { get; set; }
    public string? CustomerLastName { get; set; }
    public TrendyolAddress? ShipmentAddress { get; set; }
    public DateTime OrderDate { get; set; }
}

public class TrendyolAddress
{
    public string? Address { get; set; }
    public string? City { get; set; }
    public string? District { get; set; }
    public string? PostalCode { get; set; }
}



