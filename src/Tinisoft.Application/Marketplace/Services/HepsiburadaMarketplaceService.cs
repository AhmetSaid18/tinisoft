using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;
using Microsoft.Extensions.Configuration;
using Tinisoft.Domain.Entities;

namespace Tinisoft.Application.Marketplace.Services;

public class HepsiburadaMarketplaceService : IMarketplaceService
{
    private readonly ILogger<HepsiburadaMarketplaceService> _logger;
    private readonly HttpClient _httpClient;
    private readonly IConfiguration _configuration;
    private readonly IApplicationDbContext _dbContext;

    public HepsiburadaMarketplaceService(
        ILogger<HepsiburadaMarketplaceService> logger,
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
        _logger.LogInformation("Syncing products to Hepsiburada for integration {IntegrationId}", integration.Id);
        
        var response = new SyncProductsResponse();
        
        try
        {
            // Hepsiburada API credentials
            var apiUrl = _configuration["Marketplace:Hepsiburada:ApiUrl"] ?? "https://mpop-sit.hepsiburada.com";
            var merchantId = integration.SupplierId ?? _configuration["Marketplace:Hepsiburada:MerchantId"];
            var username = integration.ApiKey ?? _configuration["Marketplace:Hepsiburada:Username"];
            var password = integration.ApiSecret ?? _configuration["Marketplace:Hepsiburada:Password"];

            if (string.IsNullOrEmpty(username) || string.IsNullOrEmpty(password))
            {
                _logger.LogError("Hepsiburada API credentials are missing");
                response.FailedCount = productIds?.Count ?? 0;
                response.Errors.Add("Hepsiburada API credentials are missing");
                return response;
            }

            // Get products from database
            var products = productIds != null
                ? await _dbContext.Products
                    .Where(p => productIds.Contains(p.Id) && p.TenantId == integration.TenantId)
                    .ToListAsync(cancellationToken)
                : await _dbContext.Products
                    .Where(p => p.TenantId == integration.TenantId && p.IsActive)
                    .Take(100)
                    .ToListAsync(cancellationToken);

            // Configure HttpClient
            _httpClient.DefaultRequestHeaders.Clear();
            _httpClient.DefaultRequestHeaders.Add("username", username);
            _httpClient.DefaultRequestHeaders.Add("password", password);

            // Sync each product
            foreach (var product in products)
            {
                try
                {
                    // Prepare Hepsiburada product model
                    var hepsiburadaProduct = new
                    {
                        merchantId = merchantId,
                        hbSku = product.SKU ?? product.Id.ToString(),
                        merchantSku = product.SKU ?? product.Id.ToString(),
                        productName = product.Title,
                        productDescription = product.Description ?? product.ShortDescription ?? "",
                        categoryId = "default", // Should be mapped from Hepsiburada category list
                        price = product.Price,
                        availableStock = product.InventoryQuantity ?? 0,
                        cargoCompanyId = "10", // Default cargo company
                        barcode = product.Barcode ?? product.SKU,
                        images = new[]
                        {
                            new { url = product.Images?.FirstOrDefault()?.OriginalUrl ?? "" }
                        },
                        attributes = new
                        {
                            color = "",
                            size = ""
                        }
                    };

                    var json = JsonSerializer.Serialize(hepsiburadaProduct);
                    var content = new StringContent(json, Encoding.UTF8, "application/json");

                    // POST to Hepsiburada API
                    var apiResponse = await _httpClient.PostAsync(
                        $"{apiUrl}/product/api/products/",
                        content,
                        cancellationToken);

                    if (apiResponse.IsSuccessStatusCode)
                    {
                        response.SyncedCount++;
                        _logger.LogInformation("Product {ProductId} synced successfully to Hepsiburada", product.Id);
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
            _logger.LogError(ex, "Error syncing products to Hepsiburada");
            response.Errors.Add($"General error: {ex.Message}");
        }
        
        return response;
    }

    public async Task<SyncOrdersResponse> SyncOrdersAsync(MarketplaceIntegration integration, CancellationToken cancellationToken)
    {
        _logger.LogInformation("Syncing orders from Hepsiburada for integration {IntegrationId}", integration.Id);
        
        var response = new SyncOrdersResponse();
        
        try
        {
            // Hepsiburada API credentials
            var apiUrl = _configuration["Marketplace:Hepsiburada:ApiUrl"] ?? "https://mpop-sit.hepsiburada.com";
            var username = integration.ApiKey ?? _configuration["Marketplace:Hepsiburada:Username"];
            var password = integration.ApiSecret ?? _configuration["Marketplace:Hepsiburada:Password"];

            if (string.IsNullOrEmpty(username) || string.IsNullOrEmpty(password))
            {
                _logger.LogError("Hepsiburada API credentials are missing");
                response.Errors.Add("Hepsiburada API credentials are missing");
                return response;
            }

            // Configure HttpClient
            _httpClient.DefaultRequestHeaders.Clear();
            _httpClient.DefaultRequestHeaders.Add("username", username);
            _httpClient.DefaultRequestHeaders.Add("password", password);

            // Get orders from Hepsiburada
            var apiResponse = await _httpClient.GetAsync(
                $"{apiUrl}/order/api/orders?page=1&pageSize=50",
                cancellationToken);

            if (apiResponse.IsSuccessStatusCode)
            {
                var jsonResponse = await apiResponse.Content.ReadAsStringAsync(cancellationToken);
                var ordersData = JsonSerializer.Deserialize<HepsiburadaOrdersResponse>(jsonResponse);

                if (ordersData?.Orders != null)
                {
                    foreach (var hbOrder in ordersData.Orders)
                    {
                        try
                        {
                            // Check if order already exists
                            var existingOrder = await _dbContext.Orders
                                .FirstOrDefaultAsync(o => 
                                    o.TenantId == integration.TenantId && 
                                    o.OrderNumber == hbOrder.OrderNumber,
                                    cancellationToken);

                            if (existingOrder == null)
                            {
                                // Create new order
                                var newOrder = new Order
                                {
                                    TenantId = integration.TenantId,
                                    OrderNumber = hbOrder.OrderNumber,
                                    Status = MapHepsiburadaStatus(hbOrder.Status),
                                    CustomerEmail = hbOrder.CustomerEmail ?? "hepsiburada@marketplace.com",
                                    CustomerFirstName = hbOrder.CustomerFirstName,
                                    CustomerLastName = hbOrder.CustomerLastName,
                                    ShippingAddressLine1 = hbOrder.ShippingAddress?.Address,
                                    ShippingCity = hbOrder.ShippingAddress?.City,
                                    ShippingState = hbOrder.ShippingAddress?.District,
                                    ShippingCountry = "TR",
                                    TotalsJson = JsonSerializer.Serialize(new
                                    {
                                        subtotal = hbOrder.TotalAmount,
                                        tax = 0,
                                        shipping = 0,
                                        discount = 0,
                                        total = hbOrder.TotalAmount
                                    }),
                                    PaymentStatus = "Paid",
                                    CreatedAt = hbOrder.OrderDate
                                };

                                _dbContext.Orders.Add(newOrder);
                                response.SyncedCount++;
                                _logger.LogInformation("Order {OrderNumber} synced from Hepsiburada", hbOrder.OrderNumber);
                            }
                        }
                        catch (Exception ex)
                        {
                            response.FailedCount++;
                            response.Errors.Add($"Order {hbOrder.OrderNumber}: {ex.Message}");
                            _logger.LogError(ex, "Error syncing order {OrderNumber}", hbOrder.OrderNumber);
                        }
                    }

                    await _dbContext.SaveChangesAsync(cancellationToken);
                }
            }
            else
            {
                var errorContent = await apiResponse.Content.ReadAsStringAsync(cancellationToken);
                response.Errors.Add($"API Error: {errorContent}");
                _logger.LogWarning("Failed to get orders from Hepsiburada: {Error}", errorContent);
            }
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error syncing orders from Hepsiburada");
            response.Errors.Add($"General error: {ex.Message}");
        }
        
        return response;
    }

    private string MapHepsiburadaStatus(string hbStatus)
    {
        return hbStatus?.ToLower() switch
        {
            "new" => "Pending",
            "unpacked" => "Processing",
            "packed" => "Processing",
            "shipped" => "Shipped",
            "delivered" => "Delivered",
            "cancelled" => "Cancelled",
            _ => "Pending"
        };
    }
}

// Hepsiburada API response models
public class HepsiburadaOrdersResponse
{
    public List<HepsiburadaOrder>? Orders { get; set; }
    public int TotalCount { get; set; }
}

public class HepsiburadaOrder
{
    public string OrderNumber { get; set; } = string.Empty;
    public string? Status { get; set; }
    public decimal TotalAmount { get; set; }
    public string? CustomerEmail { get; set; }
    public string? CustomerFirstName { get; set; }
    public string? CustomerLastName { get; set; }
    public HepsiburadaAddress? ShippingAddress { get; set; }
    public DateTime OrderDate { get; set; }
}

public class HepsiburadaAddress
{
    public string? Address { get; set; }
    public string? City { get; set; }
    public string? District { get; set; }
}



