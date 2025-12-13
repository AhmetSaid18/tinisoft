using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Xml.Linq;
using Microsoft.Extensions.Configuration;
using Tinisoft.Domain.Entities;

namespace Tinisoft.Application.Marketplace.Services;

public class N11MarketplaceService : IMarketplaceService
{
    private readonly ILogger<N11MarketplaceService> _logger;
    private readonly HttpClient _httpClient;
    private readonly IConfiguration _configuration;
    private readonly IApplicationDbContext _dbContext;

    public N11MarketplaceService(
        ILogger<N11MarketplaceService> logger,
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
        _logger.LogInformation("Syncing products to N11 for integration {IntegrationId}", integration.Id);
        
        var response = new SyncProductsResponse();
        
        try
        {
            // N11 API credentials
            var apiUrl = _configuration["Marketplace:N11:ApiUrl"] ?? "https://api.n11.com/ws";
            var apiKey = integration.ApiKey ?? _configuration["Marketplace:N11:ApiKey"];
            var secretKey = integration.ApiSecret ?? _configuration["Marketplace:N11:SecretKey"];

            if (string.IsNullOrEmpty(apiKey) || string.IsNullOrEmpty(secretKey))
            {
                _logger.LogError("N11 API credentials are missing");
                response.FailedCount = productIds?.Count ?? 0;
                response.Errors.Add("N11 API credentials are missing");
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

            // Sync each product
            foreach (var product in products)
            {
                try
                {
                    // N11 uses SOAP/XML API
                    var xmlRequest = CreateN11ProductXml(product, apiKey, secretKey);
                    var content = new StringContent(xmlRequest, Encoding.UTF8, "text/xml");

                    // POST to N11 API
                    var apiResponse = await _httpClient.PostAsync(
                        $"{apiUrl}/ProductService.wsdl",
                        content,
                        cancellationToken);

                    if (apiResponse.IsSuccessStatusCode)
                    {
                        var xmlResponse = await apiResponse.Content.ReadAsStringAsync(cancellationToken);
                        
                        // Parse XML response to check success
                        if (xmlResponse.Contains("<result>true</result>"))
                        {
                            response.SyncedCount++;
                            _logger.LogInformation("Product {ProductId} synced successfully to N11", product.Id);
                        }
                        else
                        {
                            response.FailedCount++;
                            response.Errors.Add($"Product {product.Title}: N11 API returned failure");
                            _logger.LogWarning("Failed to sync product {ProductId}", product.Id);
                        }
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
            _logger.LogError(ex, "Error syncing products to N11");
            response.Errors.Add($"General error: {ex.Message}");
        }
        
        return response;
    }

    public async Task<SyncOrdersResponse> SyncOrdersAsync(MarketplaceIntegration integration, CancellationToken cancellationToken)
    {
        _logger.LogInformation("Syncing orders from N11 for integration {IntegrationId}", integration.Id);
        
        var response = new SyncOrdersResponse();
        
        try
        {
            // N11 API credentials
            var apiUrl = _configuration["Marketplace:N11:ApiUrl"] ?? "https://api.n11.com/ws";
            var apiKey = integration.ApiKey ?? _configuration["Marketplace:N11:ApiKey"];
            var secretKey = integration.ApiSecret ?? _configuration["Marketplace:N11:SecretKey"];

            if (string.IsNullOrEmpty(apiKey) || string.IsNullOrEmpty(secretKey))
            {
                _logger.LogError("N11 API credentials are missing");
                response.Errors.Add("N11 API credentials are missing");
                return response;
            }

            // Create XML request to get orders
            var xmlRequest = CreateN11GetOrdersXml(apiKey, secretKey);
            var content = new StringContent(xmlRequest, Encoding.UTF8, "text/xml");

            // POST to N11 API
            var apiResponse = await _httpClient.PostAsync(
                $"{apiUrl}/OrderService.wsdl",
                content,
                cancellationToken);

            if (apiResponse.IsSuccessStatusCode)
            {
                var xmlResponse = await apiResponse.Content.ReadAsStringAsync(cancellationToken);
                var xDoc = XDocument.Parse(xmlResponse);
                
                // Parse orders from XML
                var orderNodes = xDoc.Descendants("order");
                
                foreach (var orderNode in orderNodes)
                {
                    try
                    {
                        var orderNumber = orderNode.Element("orderNumber")?.Value ?? "";
                        var status = orderNode.Element("status")?.Value ?? "";
                        var totalAmount = decimal.Parse(orderNode.Element("totalAmount")?.Value ?? "0");
                        var orderDate = DateTime.Parse(orderNode.Element("orderDate")?.Value ?? DateTime.UtcNow.ToString());

                        // Check if order already exists
                        var existingOrder = await _dbContext.Orders
                            .FirstOrDefaultAsync(o => 
                                o.TenantId == integration.TenantId && 
                                o.OrderNumber == orderNumber,
                                cancellationToken);

                        if (existingOrder == null)
                        {
                            // Create new order
                            var newOrder = new Order
                            {
                                TenantId = integration.TenantId,
                                OrderNumber = orderNumber,
                                Status = MapN11Status(status),
                                CustomerEmail = orderNode.Element("customerEmail")?.Value ?? "n11@marketplace.com",
                                CustomerFirstName = orderNode.Element("customerFirstName")?.Value,
                                CustomerLastName = orderNode.Element("customerLastName")?.Value,
                                ShippingAddressLine1 = orderNode.Element("shippingAddress")?.Value,
                                ShippingCity = orderNode.Element("city")?.Value,
                                ShippingCountry = "TR",
                                TotalsJson = JsonSerializer.Serialize(new
                                {
                                    subtotal = totalAmount,
                                    tax = 0,
                                    shipping = 0,
                                    discount = 0,
                                    total = totalAmount
                                }),
                                PaymentStatus = "Paid",
                                CreatedAt = orderDate
                            };

                            _dbContext.Orders.Add(newOrder);
                            response.SyncedCount++;
                            _logger.LogInformation("Order {OrderNumber} synced from N11", orderNumber);
                        }
                    }
                    catch (Exception ex)
                    {
                        response.FailedCount++;
                        response.Errors.Add($"Order parsing error: {ex.Message}");
                        _logger.LogError(ex, "Error syncing order from N11");
                    }
                }

                await _dbContext.SaveChangesAsync(cancellationToken);
            }
            else
            {
                var errorContent = await apiResponse.Content.ReadAsStringAsync(cancellationToken);
                response.Errors.Add($"API Error: {errorContent}");
                _logger.LogWarning("Failed to get orders from N11: {Error}", errorContent);
            }
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error syncing orders from N11");
            response.Errors.Add($"General error: {ex.Message}");
        }
        
        return response;
    }

    private string CreateN11ProductXml(Product product, string apiKey, string secretKey)
    {
        // Simplified N11 SOAP XML structure
        return $@"<?xml version=""1.0"" encoding=""UTF-8""?>
<soapenv:Envelope xmlns:soapenv=""http://schemas.xmlsoap.org/soap/envelope/"" xmlns:sch=""http://www.n11.com/ws/schemas"">
    <soapenv:Header/>
    <soapenv:Body>
        <sch:SaveProductRequest>
            <auth>
                <appKey>{apiKey}</appKey>
                <appSecret>{secretKey}</appSecret>
            </auth>
            <product>
                <productSellerCode>{product.SKU ?? product.Id.ToString()}</productSellerCode>
                <title>{product.Title}</title>
                <description>{product.Description ?? product.ShortDescription}</description>
                <categoryId>1000000</categoryId>
                <price>{product.Price}</price>
                <stockItems>
                    <stockItem>
                        <quantity>{product.InventoryQuantity ?? 0}</quantity>
                        <sellerStockCode>{product.SKU}</sellerStockCode>
                        <optionPrice>{product.Price}</optionPrice>
                    </stockItem>
                </stockItems>
            </product>
        </sch:SaveProductRequest>
    </soapenv:Body>
</soapenv:Envelope>";
    }

    private string CreateN11GetOrdersXml(string apiKey, string secretKey)
    {
        return $@"<?xml version=""1.0"" encoding=""UTF-8""?>
<soapenv:Envelope xmlns:soapenv=""http://schemas.xmlsoap.org/soap/envelope/"" xmlns:sch=""http://www.n11.com/ws/schemas"">
    <soapenv:Header/>
    <soapenv:Body>
        <sch:OrderListRequest>
            <auth>
                <appKey>{apiKey}</appKey>
                <appSecret>{secretKey}</appSecret>
            </auth>
            <pagingData>
                <currentPage>0</currentPage>
                <pageSize>50</pageSize>
            </pagingData>
        </sch:OrderListRequest>
    </soapenv:Body>
</soapenv:Envelope>";
    }

    private string MapN11Status(string n11Status)
    {
        return n11Status?.ToLower() switch
        {
            "new" => "Pending",
            "in_process" => "Processing",
            "shipped" => "Shipped",
            "delivered" => "Delivered",
            "cancelled" => "Cancelled",
            _ => "Pending"
        };
    }
}



