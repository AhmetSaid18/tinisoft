using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Domain.Entities;
using Tinisoft.Application.Common.Interfaces;
using Tinisoft.Shared.Contracts;
using Tinisoft.Application.Common.Exceptions;
using Tinisoft.Application.Invoices.Services;
using Finbuckle.MultiTenant;
using Tinisoft.Shared.Events;
using Tinisoft.Shared.Contracts;
using System.Text.Json;

namespace Tinisoft.Application.Invoices.Commands.CreateInvoice;

public class CreateInvoiceCommandHandler : IRequestHandler<CreateInvoiceCommand, CreateInvoiceResponse>
{
    private readonly IApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly IInvoiceNumberGenerator _invoiceNumberGenerator;
    private readonly IUBLXMLGenerator _ublXmlGenerator;
    private readonly IGIBService _gibService;
    private readonly IPDFGenerator _pdfGenerator;
    private readonly IEventBus _eventBus;
    private readonly ILogger<CreateInvoiceCommandHandler> _logger;

    public CreateInvoiceCommandHandler(
        IApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor,
        IInvoiceNumberGenerator invoiceNumberGenerator,
        IUBLXMLGenerator ublXmlGenerator,
        IGIBService gibService,
        IPDFGenerator pdfGenerator,
        IEventBus eventBus,
        ILogger<CreateInvoiceCommandHandler> logger)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
        _invoiceNumberGenerator = invoiceNumberGenerator;
        _ublXmlGenerator = ublXmlGenerator;
        _gibService = gibService;
        _pdfGenerator = pdfGenerator;
        _eventBus = eventBus;
        _logger = logger;
    }

    public async Task<CreateInvoiceResponse> Handle(CreateInvoiceCommand request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        // Order kontrolü
        var order = await _dbContext.Orders
            .Include(o => o.OrderItems)
            .ThenInclude(oi => oi.Product)
            .Include(o => o.Customer)
            .FirstOrDefaultAsync(o => o.Id == request.OrderId && o.TenantId == tenantId, cancellationToken);

        if (order == null)
        {
            throw new NotFoundException("Sipariş", request.OrderId);
        }

        // Bu sipariş için zaten fatura var mı?
        var existingInvoice = await _dbContext.Invoices
            .FirstOrDefaultAsync(i => i.OrderId == request.OrderId && i.TenantId == tenantId, cancellationToken);

        if (existingInvoice != null)
        {
            throw new BadRequestException($"Bu sipariş için zaten bir fatura mevcut: {existingInvoice.InvoiceNumber}");
        }

        // Sipariş ödenmiş mi?
        if (order.PaymentStatus != "Paid")
        {
            throw new BadRequestException("Sadece ödenmiş siparişler için fatura kesilebilir");
        }

        // Tenant Invoice Settings
        var invoiceSettings = await _dbContext.TenantInvoiceSettings
            .FirstOrDefaultAsync(s => s.TenantId == tenantId, cancellationToken);

        if (invoiceSettings == null)
        {
            throw new BadRequestException("Fatura ayarları yapılandırılmamış. Lütfen önce fatura ayarlarını yapılandırın.");
        }

        if (!invoiceSettings.IsEFaturaUser)
        {
            throw new BadRequestException("E-fatura kullanıcısı değilsiniz. Lütfen önce e-fatura başvurusu yapın.");
        }

        // Invoice numarası oluştur
        var invoiceNumber = await _invoiceNumberGenerator.GenerateNextInvoiceNumberAsync(
            tenantId,
            invoiceSettings.InvoicePrefix,
            invoiceSettings.InvoiceSerial,
            cancellationToken);

        // Invoice oluştur
        var invoice = new Invoice
        {
            TenantId = tenantId,
            OrderId = order.Id,
            InvoiceNumber = invoiceNumber.FullNumber, // Tam format: FT20240001A
            InvoiceSerial = invoiceNumber.Serial,
            InvoiceDate = request.InvoiceDate ?? DateTime.UtcNow,
            InvoiceType = request.InvoiceType ?? invoiceSettings.DefaultInvoiceType,
            ProfileId = request.ProfileId ?? invoiceSettings.DefaultProfileId,
            Status = "Draft",
            
            // Customer Info
            CustomerName = !string.IsNullOrEmpty(order.CustomerFirstName) 
                ? $"{order.CustomerFirstName} {order.CustomerLastName}".Trim()
                : order.CustomerEmail,
            CustomerEmail = order.CustomerEmail,
            CustomerPhone = order.CustomerPhone,
            CustomerVKN = order.Customer?.Email, // TODO: Customer entity'de VKN field'ı eklenebilir
            CustomerAddressLine1 = order.ShippingAddressLine1,
            CustomerAddressLine2 = order.ShippingAddressLine2,
            CustomerCity = order.ShippingCity,
            CustomerState = order.ShippingState,
            CustomerPostalCode = order.ShippingPostalCode,
            CustomerCountry = order.ShippingCountry ?? "TR",
            
            // Totals (Order'dan parse et)
            Currency = "TRY"
        };

        // Totals'ı Order'dan al
        var totals = JsonSerializer.Deserialize<Dictionary<string, object>>(order.TotalsJson ?? "{}");
        if (totals != null)
        {
            invoice.Subtotal = totals.TryGetValue("subtotal", out var sub) && decimal.TryParse(sub.ToString(), out var subDec) ? subDec : 0;
            invoice.TaxAmount = totals.TryGetValue("tax", out var tax) && decimal.TryParse(tax.ToString(), out var taxDec) ? taxDec : 0;
            invoice.ShippingAmount = totals.TryGetValue("shipping", out var ship) && decimal.TryParse(ship.ToString(), out var shipDec) ? shipDec : 0;
            invoice.DiscountAmount = totals.TryGetValue("discount", out var disc) && decimal.TryParse(disc.ToString(), out var discDec) ? discDec : 0;
            invoice.Total = totals.TryGetValue("total", out var tot) && decimal.TryParse(tot.ToString(), out var totDec) ? totDec : 0;
        }

        invoice.PaymentMethod = order.PaymentProvider ?? "KrediKartı";
        invoice.PaymentDueDate = invoice.InvoiceDate.AddDays(invoiceSettings.PaymentDueDays);

        // Invoice Items oluştur
        var taxDetails = new List<InvoiceTaxDetailDto>();
        foreach (var orderItem in order.OrderItems.OrderBy(oi => oi.ProductId))
        {
            var product = orderItem.Product;
            var taxRate = product?.TaxRate;

            var invoiceItem = new InvoiceItem
            {
                InvoiceId = invoice.Id,
                ProductId = orderItem.ProductId,
                ProductVariantId = orderItem.ProductVariantId,
                ItemName = orderItem.Title,
                ItemCode = orderItem.SKU ?? product?.SKU,
                ProductServiceCode = taxRate?.ProductServiceCode,
                Quantity = orderItem.Quantity,
                Unit = "C62", // Adet
                UnitPrice = orderItem.UnitPrice,
                LineTotal = orderItem.TotalPrice,
                TaxRateId = taxRate?.Id,
                TaxRatePercent = taxRate?.Rate ?? 20m,
                TaxAmount = (orderItem.TotalPrice * (taxRate?.Rate ?? 20m)) / 100m,
                LineTotalWithTax = orderItem.TotalPrice + ((orderItem.TotalPrice * (taxRate?.Rate ?? 20m)) / 100m),
                Position = invoice.Items.Count + 1
            };

            invoice.Items.Add(invoiceItem);

            // Tax details için
            var existingTax = taxDetails.FirstOrDefault(t => t.TaxRatePercent == invoiceItem.TaxRatePercent);
            if (existingTax != null)
            {
                existingTax.TaxableAmount += invoiceItem.LineTotal;
                existingTax.TaxAmount += invoiceItem.TaxAmount;
            }
            else
            {
                taxDetails.Add(new InvoiceTaxDetailDto
                {
                    TaxRatePercent = invoiceItem.TaxRatePercent,
                    TaxableAmount = invoiceItem.LineTotal,
                    TaxAmount = invoiceItem.TaxAmount
                });
            }
        }

        invoice.TaxDetailsJson = JsonSerializer.Serialize(taxDetails);

        _dbContext.Invoices.Add(invoice);

        // Order'a InvoiceId ekle
        order.InvoiceId = invoice.Id;

        await _dbContext.SaveChangesAsync(cancellationToken);

        _logger.LogInformation("Invoice created: {InvoiceNumber} for Order: {OrderId}", invoice.InvoiceNumber, order.Id);

        // UBL-TR XML oluştur
        var ublXml = await _ublXmlGenerator.GenerateInvoiceXMLAsync(invoice, invoiceSettings, cancellationToken);
        invoice.UBLXML = ublXml;

        // Mali mühür ile imzala
        var signedXml = await _ublXmlGenerator.SignUBLXMLAsync(ublXml, invoiceSettings, cancellationToken);
        invoice.UBLXMLSigned = signedXml;
        invoice.Status = "ReadyToSend";

        await _dbContext.SaveChangesAsync(cancellationToken);

        // PDF oluştur (async - background)
        _ = Task.Run(async () =>
        {
            try
            {
                var pdfUrl = await _pdfGenerator.GenerateInvoicePDFAsync(invoice, invoiceSettings, cancellationToken);
                invoice.PDFUrl = pdfUrl;
                invoice.PDFGeneratedAt = DateTime.UtcNow;
                await _dbContext.SaveChangesAsync(cancellationToken);
            }
            catch (Exception ex)
            {
                _logger.LogWarning(ex, "PDF generation failed for invoice: {InvoiceId}", invoice.Id);
            }
        }, cancellationToken);

        // GİB'e gönder (eğer AutoSendToGIB ise)
        string? gibInvoiceId = null;
        if (request.AutoSendToGIB && invoiceSettings.AutoSendToGIB)
        {
            try
            {
                var gibResponse = await _gibService.SendInvoiceAsync(signedXml, invoiceSettings, cancellationToken);
                
                if (gibResponse.Success)
                {
                    invoice.GIBInvoiceId = gibResponse.InvoiceId;
                    invoice.GIBInvoiceNumber = gibResponse.InvoiceNumber;
                    invoice.GIBSentAt = DateTime.UtcNow;
                    invoice.Status = "Sent";
                    invoice.GIBApprovalStatus = "Gönderildi";
                    
                    gibInvoiceId = gibResponse.InvoiceId;
                    
                    _logger.LogInformation("Invoice sent to GİB: {InvoiceNumber}, GIB ID: {GIBInvoiceId}", 
                        invoice.InvoiceNumber, gibResponse.InvoiceId);
                }
                else
                {
                    invoice.Status = "SendFailed";
                    invoice.StatusMessage = gibResponse.ErrorMessage;
                    _logger.LogWarning("GİB send failed for invoice {InvoiceNumber}: {Error}", 
                        invoice.InvoiceNumber, gibResponse.ErrorMessage);
                }
            }
            catch (Exception ex)
            {
                invoice.Status = "SendFailed";
                invoice.StatusMessage = ex.Message;
                _logger.LogError(ex, "Error sending invoice to GİB: {InvoiceNumber}", invoice.InvoiceNumber);
            }

            await _dbContext.SaveChangesAsync(cancellationToken);
        }

        // Event publish
        await _eventBus.PublishAsync(new InvoiceCreatedEvent
        {
            InvoiceId = invoice.Id,
            OrderId = order.Id,
            TenantId = tenantId,
            InvoiceNumber = invoice.InvoiceNumber
        }, cancellationToken);

        return new CreateInvoiceResponse
        {
            InvoiceId = invoice.Id,
            InvoiceNumber = invoice.InvoiceNumber,
            InvoiceSerial = invoice.InvoiceSerial,
            Status = invoice.Status,
            GIBInvoiceId = gibInvoiceId,
            PDFUrl = invoice.PDFUrl,
            Message = invoice.Status == "Sent" 
                ? "Fatura başarıyla oluşturuldu ve GİB'e gönderildi" 
                : "Fatura başarıyla oluşturuldu"
        };
    }
}

internal class InvoiceTaxDetailDto
{
    public decimal TaxRatePercent { get; set; }
    public decimal TaxableAmount { get; set; }
    public decimal TaxAmount { get; set; }
}



