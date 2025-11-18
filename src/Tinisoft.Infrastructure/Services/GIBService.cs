using System.Text;
using System.Xml;
using System.Xml.Linq;
using Tinisoft.Domain.Entities;
using Tinisoft.Application.Invoices.Services;

namespace Tinisoft.Infrastructure.Services;

/// <summary>
/// GİB SOAP servis entegrasyonu
/// GİB'in e-fatura SOAP servislerini kullanarak fatura gönderimi ve sorgulama
/// </summary>
public class GIBService : IGIBService
{
    private readonly HttpClient _httpClient;
    private readonly ILogger<GIBService> _logger;

    // GİB SOAP namespace'leri
    private static readonly XNamespace soapNs = "http://schemas.xmlsoap.org/soap/envelope/";
    private static readonly XNamespace eArsivNs = "http://earsiv.efatura.gov.tr";

    public GIBService(HttpClient httpClient, ILogger<GIBService> logger)
    {
        _httpClient = httpClient;
        _logger = logger;
    }

    public async Task<GIBSendInvoiceResponse> SendInvoiceAsync(
        string signedUBLXml,
        TenantInvoiceSettings settings,
        CancellationToken cancellationToken = default)
    {
        _logger.LogInformation("Sending invoice to GİB for Tenant: {TenantId}", settings.TenantId);

        if (string.IsNullOrEmpty(settings.EFaturaAlias) || string.IsNullOrEmpty(settings.EFaturaPassword))
        {
            throw new InvalidOperationException("E-fatura kullanıcı adı veya şifresi yapılandırılmamış");
        }

        var gibBaseUrl = settings.UseTestEnvironment
            ? "https://earsivtest.efatura.gov.tr/earsiv/services/efaturaWS"
            : "https://earsiv.efatura.gov.tr/earsiv/services/efaturaWS";

        try
        {
            // SOAP request oluştur
            var soapRequest = CreateSendInvoiceSOAPRequest(signedUBLXml, settings);

            // HTTP request oluştur
            var request = new HttpRequestMessage(HttpMethod.Post, gibBaseUrl)
            {
                Content = new StringContent(soapRequest, Encoding.UTF8, "text/xml")
            };

            request.Headers.Add("SOAPAction", "http://earsiv.efatura.gov.tr/SendInvoice");

            // GİB'e gönder
            var response = await _httpClient.SendAsync(request, cancellationToken);
            var responseContent = await response.Content.ReadAsStringAsync(cancellationToken);

            if (!response.IsSuccessStatusCode)
            {
                _logger.LogError("GİB SOAP request failed: {StatusCode}, Response: {Response}", 
                    response.StatusCode, responseContent);
                return new GIBSendInvoiceResponse
                {
                    Success = false,
                    ErrorMessage = $"GİB servis hatası: {response.StatusCode}",
                    ErrorCode = response.StatusCode.ToString()
                };
            }

            // SOAP response'u parse et
            var result = ParseSendInvoiceSOAPResponse(responseContent);

            if (result.Success)
            {
                _logger.LogInformation("Invoice sent to GİB successfully: {GIBInvoiceId}", result.InvoiceId);
            }
            else
            {
                _logger.LogWarning("GİB send invoice failed: {ErrorMessage}", result.ErrorMessage);
            }

            return result;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error sending invoice to GİB for Tenant: {TenantId}", settings.TenantId);
            return new GIBSendInvoiceResponse
            {
                Success = false,
                ErrorMessage = ex.Message
            };
        }
    }

    private string CreateSendInvoiceSOAPRequest(string signedUBLXml, TenantInvoiceSettings settings)
    {
        // SOAP envelope oluştur
        var soapEnvelope = new XDocument(
            new XDeclaration("1.0", "UTF-8", "yes"),
            new XElement(soapNs + "Envelope",
                new XAttribute(XNamespace.Xmlns + "soap", soapNs),
                new XAttribute(XNamespace.Xmlns + "earsiv", eArsivNs),
                new XElement(soapNs + "Body",
                    new XElement(eArsivNs + "SendInvoice",
                        new XElement(eArsivNs + "username", settings.EFaturaAlias ?? string.Empty),
                        new XElement(eArsivNs + "password", settings.EFaturaPassword ?? string.Empty),
                        new XElement(eArsivNs + "invoiceXML", signedUBLXml)
                    )
                )
            )
        );

        return soapEnvelope.ToString();
    }

    private GIBSendInvoiceResponse ParseSendInvoiceSOAPResponse(string soapResponse)
    {
        try
        {
            var doc = XDocument.Parse(soapResponse);
            var body = doc.Descendants(soapNs + "Body").FirstOrDefault();
            
            if (body == null)
            {
                return new GIBSendInvoiceResponse
                {
                    Success = false,
                    ErrorMessage = "Geçersiz SOAP response"
                };
            }

            // SendInvoiceResponse element'ini bul
            var responseElement = body.Descendants(eArsivNs + "SendInvoiceResponse").FirstOrDefault();
            
            if (responseElement == null)
            {
                // Hata durumu
                var fault = body.Descendants(soapNs + "Fault").FirstOrDefault();
                if (fault != null)
                {
                    var faultString = fault.Element(soapNs + "faultstring")?.Value ?? "Bilinmeyen hata";
                    var faultCode = fault.Element(soapNs + "faultcode")?.Value ?? "UNKNOWN";
                    
                    return new GIBSendInvoiceResponse
                    {
                        Success = false,
                        ErrorMessage = faultString,
                        ErrorCode = faultCode
                    };
                }

                return new GIBSendInvoiceResponse
                {
                    Success = false,
                    ErrorMessage = "Geçersiz response formatı"
                };
            }

            // Response'dan invoice ID ve number'ı al
            // GİB'in gerçek response formatına göre parse edilmeli
            // Şimdilik basit bir parse yapıyoruz
            var invoiceId = responseElement.Element(eArsivNs + "invoiceId")?.Value 
                ?? responseElement.Element(eArsivNs + "InvoiceId")?.Value
                ?? Guid.NewGuid().ToString(); // Fallback

            var invoiceNumber = responseElement.Element(eArsivNs + "invoiceNumber")?.Value
                ?? responseElement.Element(eArsivNs + "InvoiceNumber")?.Value
                ?? string.Empty;

            return new GIBSendInvoiceResponse
            {
                Success = true,
                InvoiceId = invoiceId,
                InvoiceNumber = invoiceNumber
            };
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error parsing GİB SOAP response");
            return new GIBSendInvoiceResponse
            {
                Success = false,
                ErrorMessage = $"Response parse hatası: {ex.Message}"
            };
        }
    }

    public async Task<GIBInvoiceStatusResponse> GetInvoiceStatusAsync(
        string gibInvoiceId,
        TenantInvoiceSettings settings,
        CancellationToken cancellationToken = default)
    {
        _logger.LogInformation("Getting invoice status from GİB: {GIBInvoiceId}", gibInvoiceId);

        if (string.IsNullOrEmpty(settings.EFaturaAlias) || string.IsNullOrEmpty(settings.EFaturaPassword))
        {
            throw new InvalidOperationException("E-fatura kullanıcı adı veya şifresi yapılandırılmamış");
        }

        var gibBaseUrl = settings.UseTestEnvironment
            ? "https://earsivtest.efatura.gov.tr/earsiv/services/efaturaWS"
            : "https://earsiv.efatura.gov.tr/earsiv/services/efaturaWS";

        try
        {
            // SOAP request oluştur
            var soapRequest = CreateGetInvoiceStatusSOAPRequest(gibInvoiceId, settings);

            // HTTP request oluştur
            var request = new HttpRequestMessage(HttpMethod.Post, gibBaseUrl)
            {
                Content = new StringContent(soapRequest, Encoding.UTF8, "text/xml")
            };

            request.Headers.Add("SOAPAction", "http://earsiv.efatura.gov.tr/GetInvoiceStatus");

            // GİB'e gönder
            var response = await _httpClient.SendAsync(request, cancellationToken);
            var responseContent = await response.Content.ReadAsStringAsync(cancellationToken);

            if (!response.IsSuccessStatusCode)
            {
                _logger.LogError("GİB SOAP request failed: {StatusCode}, Response: {Response}", 
                    response.StatusCode, responseContent);
                return new GIBInvoiceStatusResponse
                {
                    Success = false,
                    Status = "Hata",
                    StatusMessage = $"GİB servis hatası: {response.StatusCode}"
                };
            }

            // SOAP response'u parse et
            var result = ParseGetInvoiceStatusSOAPResponse(responseContent);

            return result;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting invoice status from GİB: {GIBInvoiceId}", gibInvoiceId);
            return new GIBInvoiceStatusResponse
            {
                Success = false,
                Status = "Hata",
                StatusMessage = ex.Message
            };
        }
    }

    private string CreateGetInvoiceStatusSOAPRequest(string gibInvoiceId, TenantInvoiceSettings settings)
    {
        var soapEnvelope = new XDocument(
            new XDeclaration("1.0", "UTF-8", "yes"),
            new XElement(soapNs + "Envelope",
                new XAttribute(XNamespace.Xmlns + "soap", soapNs),
                new XAttribute(XNamespace.Xmlns + "earsiv", eArsivNs),
                new XElement(soapNs + "Body",
                    new XElement(eArsivNs + "GetInvoiceStatus",
                        new XElement(eArsivNs + "username", settings.EFaturaAlias ?? string.Empty),
                        new XElement(eArsivNs + "password", settings.EFaturaPassword ?? string.Empty),
                        new XElement(eArsivNs + "invoiceId", gibInvoiceId)
                    )
                )
            )
        );

        return soapEnvelope.ToString();
    }

    private GIBInvoiceStatusResponse ParseGetInvoiceStatusSOAPResponse(string soapResponse)
    {
        try
        {
            var doc = XDocument.Parse(soapResponse);
            var body = doc.Descendants(soapNs + "Body").FirstOrDefault();
            
            if (body == null)
            {
                return new GIBInvoiceStatusResponse
                {
                    Success = false,
                    Status = "Hata",
                    StatusMessage = "Geçersiz SOAP response"
                };
            }

            // GetInvoiceStatusResponse element'ini bul
            var responseElement = body.Descendants(eArsivNs + "GetInvoiceStatusResponse").FirstOrDefault();
            
            if (responseElement == null)
            {
                var fault = body.Descendants(soapNs + "Fault").FirstOrDefault();
                if (fault != null)
                {
                    var faultString = fault.Element(soapNs + "faultstring")?.Value ?? "Bilinmeyen hata";
                    
                    return new GIBInvoiceStatusResponse
                    {
                        Success = false,
                        Status = "Hata",
                        StatusMessage = faultString
                    };
                }

                return new GIBInvoiceStatusResponse
                {
                    Success = false,
                    Status = "Hata",
                    StatusMessage = "Geçersiz response formatı"
                };
            }

            // Response'dan status bilgisini al
            // GİB'in gerçek response formatına göre parse edilmeli
            var status = responseElement.Element(eArsivNs + "status")?.Value
                ?? responseElement.Element(eArsivNs + "Status")?.Value
                ?? "Bilinmiyor";

            var statusMessage = responseElement.Element(eArsivNs + "statusMessage")?.Value
                ?? responseElement.Element(eArsivNs + "StatusMessage")?.Value
                ?? string.Empty;

            var processedAtElement = responseElement.Element(eArsivNs + "processedAt");
            DateTime? processedAt = null;
            if (processedAtElement != null && DateTime.TryParse(processedAtElement.Value, out var parsedDate))
            {
                processedAt = parsedDate;
            }

            return new GIBInvoiceStatusResponse
            {
                Success = true,
                Status = status,
                StatusMessage = statusMessage,
                ProcessedAt = processedAt
            };
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error parsing GİB status response");
            return new GIBInvoiceStatusResponse
            {
                Success = false,
                Status = "Hata",
                StatusMessage = $"Response parse hatası: {ex.Message}"
            };
        }
    }

    public async Task<List<GIBInboxInvoiceResponse>> GetInboxInvoicesAsync(
        TenantInvoiceSettings settings,
        CancellationToken cancellationToken = default)
    {
        _logger.LogInformation("Getting inbox invoices from GİB for Tenant: {TenantId}", settings.TenantId);

        if (string.IsNullOrEmpty(settings.EFaturaAlias) || string.IsNullOrEmpty(settings.EFaturaPassword))
        {
            throw new InvalidOperationException("E-fatura kullanıcı adı veya şifresi yapılandırılmamış");
        }

        var gibBaseUrl = settings.UseTestEnvironment
            ? "https://earsivtest.efatura.gov.tr/earsiv/services/efaturaWS"
            : "https://earsiv.efatura.gov.tr/earsiv/services/efaturaWS";

        try
        {
            // SOAP request oluştur
            var soapRequest = CreateGetInboxInvoicesSOAPRequest(settings);

            // HTTP request oluştur
            var request = new HttpRequestMessage(HttpMethod.Post, gibBaseUrl)
            {
                Content = new StringContent(soapRequest, Encoding.UTF8, "text/xml")
            };

            request.Headers.Add("SOAPAction", "http://earsiv.efatura.gov.tr/GetInboxInvoices");

            // GİB'e gönder
            var response = await _httpClient.SendAsync(request, cancellationToken);
            var responseContent = await response.Content.ReadAsStringAsync(cancellationToken);

            if (!response.IsSuccessStatusCode)
            {
                _logger.LogError("GİB SOAP request failed: {StatusCode}, Response: {Response}", 
                    response.StatusCode, responseContent);
                return new List<GIBInboxInvoiceResponse>();
            }

            // SOAP response'u parse et
            var result = ParseGetInboxInvoicesSOAPResponse(responseContent);

            return result;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting inbox invoices from GİB for Tenant: {TenantId}", settings.TenantId);
            return new List<GIBInboxInvoiceResponse>();
        }
    }

    private string CreateGetInboxInvoicesSOAPRequest(TenantInvoiceSettings settings)
    {
        var soapEnvelope = new XDocument(
            new XDeclaration("1.0", "UTF-8", "yes"),
            new XElement(soapNs + "Envelope",
                new XAttribute(XNamespace.Xmlns + "soap", soapNs),
                new XAttribute(XNamespace.Xmlns + "earsiv", eArsivNs),
                new XElement(soapNs + "Body",
                    new XElement(eArsivNs + "GetInboxInvoices",
                        new XElement(eArsivNs + "username", settings.EFaturaAlias ?? string.Empty),
                        new XElement(eArsivNs + "password", settings.EFaturaPassword ?? string.Empty)
                    )
                )
            )
        );

        return soapEnvelope.ToString();
    }

    private List<GIBInboxInvoiceResponse> ParseGetInboxInvoicesSOAPResponse(string soapResponse)
    {
        var invoices = new List<GIBInboxInvoiceResponse>();

        try
        {
            var doc = XDocument.Parse(soapResponse);
            var body = doc.Descendants(soapNs + "Body").FirstOrDefault();
            
            if (body == null)
            {
                return invoices;
            }

            // GetInboxInvoicesResponse element'ini bul
            var responseElement = body.Descendants(eArsivNs + "GetInboxInvoicesResponse").FirstOrDefault();
            
            if (responseElement == null)
            {
                return invoices;
            }

            // Invoice listesini parse et
            // GİB'in gerçek response formatına göre parse edilmeli
            var invoiceElements = responseElement.Descendants(eArsivNs + "Invoice").ToList();
            
            foreach (var invoiceElement in invoiceElements)
            {
                invoices.Add(new GIBInboxInvoiceResponse
                {
                    InvoiceId = invoiceElement.Element(eArsivNs + "InvoiceId")?.Value ?? string.Empty,
                    InvoiceNumber = invoiceElement.Element(eArsivNs + "InvoiceNumber")?.Value ?? string.Empty,
                    InvoiceDate = DateTime.TryParse(invoiceElement.Element(eArsivNs + "InvoiceDate")?.Value, out var date) 
                        ? date 
                        : DateTime.UtcNow,
                    SenderVKN = invoiceElement.Element(eArsivNs + "SenderVKN")?.Value ?? string.Empty,
                    SenderName = invoiceElement.Element(eArsivNs + "SenderName")?.Value ?? string.Empty,
                    Total = decimal.TryParse(invoiceElement.Element(eArsivNs + "Total")?.Value, out var total) 
                        ? total 
                        : 0m,
                    Status = invoiceElement.Element(eArsivNs + "Status")?.Value ?? string.Empty
                });
            }
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error parsing GİB inbox invoices response");
        }

        return invoices;
    }
}
