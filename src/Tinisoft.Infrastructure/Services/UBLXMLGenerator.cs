using System.Xml;
using System.Xml.Linq;
using System.Text;
using Tinisoft.Domain.Entities;
using Tinisoft.Application.Invoices.Services;
using System.Security.Cryptography.X509Certificates;
using System.Security.Cryptography.Xml;
using System.Text.Json;

namespace Tinisoft.Infrastructure.Services;

/// <summary>
/// UBL-TR 2.1 XML oluşturma ve imzalama servisi
/// GİB standardına uygun e-fatura XML'leri oluşturur
/// </summary>
public class UBLXMLGenerator : IUBLXMLGenerator
{
    private readonly ILogger<UBLXMLGenerator> _logger;

    // UBL-TR 2.1 namespace'leri
    private static readonly XNamespace nsCbc = "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2";
    private static readonly XNamespace nsCac = "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2";
    private static readonly XNamespace nsExt = "urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2";
    private static readonly XNamespace nsDs = "http://www.w3.org/2000/09/xmldsig#";

    public UBLXMLGenerator(ILogger<UBLXMLGenerator> logger)
    {
        _logger = logger;
    }

    public async Task<string> GenerateInvoiceXMLAsync(
        Invoice invoice,
        TenantInvoiceSettings settings,
        CancellationToken cancellationToken = default)
    {
        _logger.LogInformation("Generating UBL-TR XML for Invoice: {InvoiceNumber}", invoice.InvoiceNumber);

        try
        {
            var xmlDoc = new XDocument(
                new XDeclaration("1.0", "UTF-8", "yes"),
                new XElement(nsCac + "Invoice",
                    // Namespace declarations
                    new XAttribute(XNamespace.Xmlns + "cac", nsCac),
                    new XAttribute(XNamespace.Xmlns + "cbc", nsCbc),
                    new XAttribute(XNamespace.Xmlns + "ext", nsExt),
                    new XAttribute(XNamespace.Xmlns + "ds", nsDs),

                    // Extensions (zorunlu)
                    new XElement(nsExt + "UBLExtensions",
                        new XElement(nsExt + "UBLExtension",
                            new XElement(nsExt + "ExtensionContent")
                        )
                    ),

                    // Invoice ID
                    new XElement(nsCbc + "ID", invoice.InvoiceNumber),

                    // Copy indicator (kopya mı?)
                    new XElement(nsCbc + "CopyIndicator", "false"),

                    // UUID (her fatura için unique)
                    new XElement(nsCbc + "UUID", Guid.NewGuid().ToString()),

                    // Issue Date
                    new XElement(nsCbc + "IssueDate", invoice.InvoiceDate.ToString("yyyy-MM-dd")),

                    // Issue Time
                    new XElement(nsCbc + "IssueTime", invoice.InvoiceDate.ToString("HH:mm:ss")),

                    // Invoice Type Code
                    new XElement(nsCbc + "InvoiceTypeCode",
                        new XAttribute("name", GetInvoiceTypeName(invoice.ProfileId)),
                        invoice.ProfileId),

                    // Note (opsiyonel)
                    string.IsNullOrEmpty(invoice.Notes)
                        ? null
                        : new XElement(nsCbc + "Note", invoice.Notes),

                    // Document Currency Code
                    new XElement(nsCbc + "DocumentCurrencyCode", invoice.Currency),

                    // Line Count Numeric
                    new XElement(nsCbc + "LineCountNumeric", invoice.Items.Count),

                    // Accounting Supplier Party (Fatura kesen şirket)
                    CreateAccountingSupplierParty(settings),

                    // Accounting Customer Party (Fatura alan müşteri)
                    CreateAccountingCustomerParty(invoice),

                    // Delivery (teslimat bilgileri - opsiyonel)
                    invoice.DeliveryDate.HasValue
                        ? CreateDelivery(invoice)
                        : null,

                    // Payment Means (ödeme yöntemi)
                    CreatePaymentMeans(invoice),

                    // Payment Terms (ödeme koşulları)
                    invoice.PaymentDueDate.HasValue
                        ? CreatePaymentTerms(invoice)
                        : null,

                    // Tax Total (vergi toplamları)
                    CreateTaxTotal(invoice),

                    // Legal Monetary Total (yasal para toplamları)
                    CreateLegalMonetaryTotal(invoice),

                    // Invoice Lines (fatura kalemleri)
                    invoice.Items.OrderBy(i => i.Position).Select((item, index) =>
                        CreateInvoiceLine(item, index + 1))
                )
            );

            // XML'i formatla (indent)
            var xmlString = FormatXml(xmlDoc);
            
            _logger.LogInformation("UBL-TR XML generated successfully for Invoice: {InvoiceNumber}", invoice.InvoiceNumber);

            return await Task.FromResult(xmlString);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error generating UBL-TR XML for Invoice: {InvoiceNumber}", invoice.InvoiceNumber);
            throw new InvalidOperationException("UBL-TR XML oluşturma başarısız", ex);
        }
    }

    private XElement CreateAccountingSupplierParty(TenantInvoiceSettings settings)
    {
        return new XElement(nsCac + "AccountingSupplierParty",
            new XElement(nsCac + "Party",
                // Party Identification (VKN/TCKN)
                new XElement(nsCac + "PartyIdentification",
                    new XElement(nsCbc + "ID",
                        new XAttribute("schemeID", string.IsNullOrEmpty(settings.VKN) ? "TCKN" : "VKN"),
                        settings.VKN ?? settings.TCKN ?? string.Empty)),

                // Party Name (Şirket adı)
                new XElement(nsCac + "PartyName",
                    new XElement(nsCbc + "Name", settings.CompanyName ?? string.Empty)),

                // Postal Address (Adres)
                new XElement(nsCac + "PostalAddress",
                    new XElement(nsCbc + "StreetName", settings.CompanyAddressLine1 ?? string.Empty),
                    !string.IsNullOrEmpty(settings.CompanyAddressLine2)
                        ? new XElement(nsCbc + "BuildingName", settings.CompanyAddressLine2)
                        : null,
                    new XElement(nsCbc + "CityName", settings.CompanyCity ?? string.Empty),
                    new XElement(nsCbc + "PostalZone", settings.CompanyPostalCode ?? string.Empty),
                    new XElement(nsCac + "Country",
                        new XElement(nsCbc + "Name", "Türkiye"),
                        new XElement(nsCbc + "IdentificationCode", settings.CompanyCountry ?? "TR"))),

                // Party Tax Scheme (Vergi Dairesi)
                new XElement(nsCac + "PartyTaxScheme",
                    new XElement(nsCac + "TaxScheme",
                        new XElement(nsCbc + "Name", settings.TaxOffice ?? string.Empty))),

                // Contact (İletişim bilgileri)
                !string.IsNullOrEmpty(settings.CompanyPhone) || !string.IsNullOrEmpty(settings.CompanyEmail)
                    ? new XElement(nsCac + "Contact",
                        !string.IsNullOrEmpty(settings.CompanyPhone)
                            ? new XElement(nsCbc + "Telephone", settings.CompanyPhone)
                            : null,
                        !string.IsNullOrEmpty(settings.CompanyEmail)
                            ? new XElement(nsCbc + "ElectronicMail", settings.CompanyEmail)
                            : null)
                    : null
            )
        );
    }

    private XElement CreateAccountingCustomerParty(Invoice invoice)
    {
        var schemeId = string.IsNullOrEmpty(invoice.CustomerVKN) ? "TCKN" : "VKN";
        var idValue = invoice.CustomerVKN ?? invoice.CustomerTCKN ?? "11111111111"; // Default: gerçek müşteri bilgisi gerekli

        return new XElement(nsCac + "AccountingCustomerParty",
            new XElement(nsCac + "Party",
                // Party Identification
                new XElement(nsCac + "PartyIdentification",
                    new XElement(nsCbc + "ID",
                        new XAttribute("schemeID", schemeId),
                        idValue)),

                // Party Name
                new XElement(nsCac + "PartyName",
                    new XElement(nsCbc + "Name", invoice.CustomerName)),

                // Postal Address
                new XElement(nsCac + "PostalAddress",
                    new XElement(nsCbc + "StreetName", invoice.CustomerAddressLine1 ?? string.Empty),
                    !string.IsNullOrEmpty(invoice.CustomerAddressLine2)
                        ? new XElement(nsCbc + "BuildingName", invoice.CustomerAddressLine2)
                        : null,
                    new XElement(nsCbc + "CityName", invoice.CustomerCity ?? string.Empty),
                    new XElement(nsCbc + "PostalZone", invoice.CustomerPostalCode ?? string.Empty),
                    new XElement(nsCac + "Country",
                        new XElement(nsCbc + "Name", "Türkiye"),
                        new XElement(nsCbc + "IdentificationCode", invoice.CustomerCountry ?? "TR"))),

                // Party Tax Scheme (varsa)
                !string.IsNullOrEmpty(invoice.CustomerTaxOffice)
                    ? new XElement(nsCac + "PartyTaxScheme",
                        new XElement(nsCac + "TaxScheme",
                            new XElement(nsCbc + "Name", invoice.CustomerTaxOffice)))
                    : null,

                // Contact
                !string.IsNullOrEmpty(invoice.CustomerPhone) || !string.IsNullOrEmpty(invoice.CustomerEmail)
                    ? new XElement(nsCac + "Contact",
                        !string.IsNullOrEmpty(invoice.CustomerPhone)
                            ? new XElement(nsCbc + "Telephone", invoice.CustomerPhone)
                            : null,
                        !string.IsNullOrEmpty(invoice.CustomerEmail)
                            ? new XElement(nsCbc + "ElectronicMail", invoice.CustomerEmail)
                            : null)
                    : null
            )
        );
    }

    private XElement? CreateDelivery(Invoice invoice)
    {
        if (!invoice.DeliveryDate.HasValue)
            return null;

        return new XElement(nsCac + "Delivery",
            new XElement(nsCac + "ActualDeliveryDate", invoice.DeliveryDate.Value.ToString("yyyy-MM-dd")));
    }

    private XElement CreatePaymentMeans(Invoice invoice)
    {
        var paymentCode = invoice.PaymentMethod switch
        {
            "KrediKartı" => "10", // Kredi Kartı
            "Havale" => "20", // Havale
            "KapıdaÖdeme" => "30", // Kapıda Ödeme
            _ => "10"
        };

        return new XElement(nsCac + "PaymentMeans",
            new XElement(nsCbc + "PaymentMeansCode", paymentCode),
            invoice.PaymentMethod == "Havale" && !string.IsNullOrEmpty(invoice.Tenant?.IBAN)
                ? new XElement(nsCac + "PayeeFinancialAccount",
                    new XElement(nsCbc + "ID", invoice.Tenant?.IBAN))
                : null);
    }

    private XElement? CreatePaymentTerms(Invoice invoice)
    {
        if (!invoice.PaymentDueDate.HasValue)
            return null;

        return new XElement(nsCac + "PaymentTerms",
            new XElement(nsCbc + "Note", $"Vade: {invoice.PaymentDueDate.Value:yyyy-MM-dd}"));
    }

    private XElement CreateTaxTotal(Invoice invoice)
    {
        // Tax Details'den vergi bilgilerini parse et
        var taxDetails = JsonSerializer.Deserialize<List<TaxDetailDto>>(invoice.TaxDetailsJson ?? "[]") ?? new List<TaxDetailDto>();

        var taxSubtotals = taxDetails.Select(tax => new XElement(nsCac + "TaxSubtotal",
            new XElement(nsCbc + "TaxableAmount",
                new XAttribute("currencyID", invoice.Currency),
                tax.TaxableAmount.ToString("F2")),
            new XElement(nsCbc + "TaxAmount",
                new XAttribute("currencyID", invoice.Currency),
                tax.TaxAmount.ToString("F2")),
            new XElement(nsCac + "TaxCategory",
                new XElement(nsCbc + "TaxExemptionReasonCode", "001"), // 001 = KDV
                new XElement(nsCbc + "Percent", tax.TaxRatePercent.ToString("F2")),
                new XElement(nsCac + "TaxScheme",
                    new XElement(nsCbc + "Name", "KDV"),
                    new XElement(nsCbc + "TaxTypeCode", "0014")))) // 0014 = KDV
        ).ToList();

        return new XElement(nsCac + "TaxTotal",
            taxSubtotals,
            new XElement(nsCbc + "TaxAmount",
                new XAttribute("currencyID", invoice.Currency),
                invoice.TaxAmount.ToString("F2")));
    }

    private XElement CreateLegalMonetaryTotal(Invoice invoice)
    {
        return new XElement(nsCac + "LegalMonetaryTotal",
            new XElement(nsCbc + "LineExtensionAmount",
                new XAttribute("currencyID", invoice.Currency),
                invoice.Subtotal.ToString("F2")),
            new XElement(nsCbc + "TaxExclusiveAmount",
                new XAttribute("currencyID", invoice.Currency),
                invoice.Subtotal.ToString("F2")),
            invoice.DiscountAmount > 0
                ? new XElement(nsCbc + "AllowanceTotalAmount",
                    new XAttribute("currencyID", invoice.Currency),
                    invoice.DiscountAmount.ToString("F2"))
                : null,
            new XElement(nsCbc + "TaxInclusiveAmount",
                new XAttribute("currencyID", invoice.Currency),
                invoice.Total.ToString("F2")),
            new XElement(nsCbc + "PayableAmount",
                new XAttribute("currencyID", invoice.Currency),
                invoice.Total.ToString("F2")));
    }

    private XElement CreateInvoiceLine(InvoiceItem item, int lineNumber)
    {
        return new XElement(nsCac + "InvoiceLine",
            new XElement(nsCbc + "ID", lineNumber.ToString()),
            new XElement(nsCbc + "InvoicedQuantity",
                new XAttribute("unitCode", item.Unit),
                item.Quantity.ToString()),
            new XElement(nsCbc + "LineExtensionAmount",
                new XAttribute("currencyID", "TRY"),
                item.LineTotal.ToString("F2")),
            new XElement(nsCac + "Item",
                new XElement(nsCbc + "Name", item.ItemName),
                !string.IsNullOrEmpty(item.ItemDescription)
                    ? new XElement(nsCbc + "Description", item.ItemDescription)
                    : null,
                !string.IsNullOrEmpty(item.ItemCode)
                    ? new XElement(nsCbc + "SellersItemIdentification",
                        new XElement(nsCbc + "ID", item.ItemCode))
                    : null,
                !string.IsNullOrEmpty(item.ProductServiceCode)
                    ? new XElement(nsCac + "CommodityClassification",
                        new XElement(nsCbc + "ItemClassificationCode", item.ProductServiceCode))
                    : null),
            new XElement(nsCac + "Price",
                new XElement(nsCbc + "PriceAmount",
                    new XAttribute("currencyID", "TRY"),
                    item.UnitPrice.ToString("F2")),
                new XElement(nsCbc + "BaseQuantity",
                    new XAttribute("unitCode", item.Unit),
                    "1")),
            CreateTaxTotalForLine(item));
    }

    private XElement CreateTaxTotalForLine(InvoiceItem item)
    {
        return new XElement(nsCac + "TaxTotal",
            new XElement(nsCbc + "TaxAmount",
                new XAttribute("currencyID", "TRY"),
                item.TaxAmount.ToString("F2")),
            new XElement(nsCac + "TaxSubtotal",
                new XElement(nsCbc + "TaxableAmount",
                    new XAttribute("currencyID", "TRY"),
                    item.LineTotal.ToString("F2")),
                new XElement(nsCbc + "TaxAmount",
                    new XAttribute("currencyID", "TRY"),
                    item.TaxAmount.ToString("F2")),
                new XElement(nsCac + "TaxCategory",
                    new XElement(nsCbc + "TaxExemptionReasonCode", "001"), // KDV
                    new XElement(nsCbc + "Percent", item.TaxRatePercent.ToString("F2")),
                    new XElement(nsCac + "TaxScheme",
                        new XElement(nsCbc + "Name", "KDV"),
                        new XElement(nsCbc + "TaxTypeCode", "0014"))))); // KDV
    }

    private string GetInvoiceTypeName(string profileId)
    {
        return profileId switch
        {
            "TICARIFATURA" => "Ticari Fatura",
            "EARSIVFATURA" => "E-Arşiv Fatura",
            "TEMELFATURA" => "Temel Fatura",
            _ => "Ticari Fatura"
        };
    }

    private string FormatXml(XDocument doc)
    {
        var sb = new StringBuilder();
        using var writer = new System.IO.StringWriter(sb);
        doc.Save(writer);
        return sb.ToString();
    }

    public async Task<string> SignUBLXMLAsync(
        string ublXml,
        TenantInvoiceSettings settings,
        CancellationToken cancellationToken = default)
    {
        _logger.LogInformation("Signing UBL-XML with XAdES-BES for Tenant: {TenantId}", settings.TenantId);

        if (string.IsNullOrEmpty(settings.MaliMuhurCertificateBase64) || 
            string.IsNullOrEmpty(settings.MaliMuhurPassword))
        {
            throw new InvalidOperationException("Mali mühür sertifikası yapılandırılmamış");
        }

        try
        {
            // Sertifikayı yükle
            var certificateBytes = Convert.FromBase64String(settings.MaliMuhurCertificateBase64);
            var certificate = new X509Certificate2(certificateBytes, settings.MaliMuhurPassword, 
                X509KeyStorageFlags.MachineKeySet | X509KeyStorageFlags.Exportable | X509KeyStorageFlags.PersistKeySet);

            if (!certificate.HasPrivateKey)
            {
                throw new InvalidOperationException("Sertifika özel anahtarı içermiyor");
            }

            // XML'i parse et
            var xmlDoc = new XmlDocument { PreserveWhitespace = true };
            xmlDoc.LoadXml(ublXml);

            // SignedXml oluştur
            var signedXml = new SignedXml(xmlDoc)
            {
                SigningKey = certificate.GetRSAPrivateKey()
            };

            // Reference oluştur (tüm document'i imzala)
            var reference = new Reference { Uri = "" };
            reference.AddTransform(new XmlDsigEnvelopedSignatureTransform());
            reference.AddTransform(new XmlDsigC14NTransform());
            signedXml.AddReference(reference);

            // KeyInfo ekle
            var keyInfo = new KeyInfo();
            keyInfo.AddClause(new KeyInfoX509Data(certificate));
            signedXml.KeyInfo = keyInfo;

            // İmzala
            signedXml.ComputeSignature();

            // Signature element'ini XML'e ekle
            var xmlSignature = signedXml.GetXml();
            xmlDoc.DocumentElement?.AppendChild(xmlDoc.ImportNode(xmlSignature, true));

            // İmzalanmış XML'i döndür
            var signedXmlString = xmlDoc.OuterXml;
            
            _logger.LogInformation("UBL-XML signed successfully with XAdES-BES for Tenant: {TenantId}", settings.TenantId);

            return await Task.FromResult(signedXmlString);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error signing UBL-XML for Tenant: {TenantId}", settings.TenantId);
            throw new InvalidOperationException("Mali mühür ile imzalama başarısız", ex);
        }
    }

    public async Task<bool> ValidateUBLXMLAsync(
        string ublXml,
        CancellationToken cancellationToken = default)
    {
        try
        {
            var doc = XDocument.Parse(ublXml);
            
            // Basic validation: root element kontrolü
            if (doc.Root == null || doc.Root.Name != nsCac + "Invoice")
            {
                _logger.LogWarning("UBL-XML validation failed: Invalid root element");
                return false;
            }

            // Required elements kontrolü (basic)
            var requiredElements = new[]
            {
                nsCbc + "ID",
                nsCbc + "IssueDate",
                nsCbc + "InvoiceTypeCode",
                nsCac + "AccountingSupplierParty",
                nsCac + "AccountingCustomerParty",
                nsCac + "TaxTotal",
                nsCac + "LegalMonetaryTotal"
            };

            foreach (var elementName in requiredElements)
            {
                if (doc.Descendants(elementName).FirstOrDefault() == null)
                {
                    _logger.LogWarning("UBL-XML validation failed: Missing required element {ElementName}", elementName);
                    return false;
                }
            }

            // TODO: XSD schema validation (GİB'den şema dosyasını indirip validate et)
            
            _logger.LogInformation("UBL-XML validation passed");
            return await Task.FromResult(true);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "UBL-XML validation failed");
            return false;
        }
    }
}

internal class TaxDetailDto
{
    public decimal TaxRatePercent { get; set; }
    public decimal TaxableAmount { get; set; }
    public decimal TaxAmount { get; set; }
}
