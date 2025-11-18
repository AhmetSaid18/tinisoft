using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Infrastructure.Persistence;
using Tinisoft.Application.Common.Exceptions;
using Finbuckle.MultiTenant;
using Tinisoft.Shared.Events;
using Tinisoft.Shared.Contracts;
using Tinisoft.Application.Invoices.Services;

namespace Tinisoft.Application.Invoices.Commands.SendInvoiceToGIB;

public class SendInvoiceToGIBCommandHandler : IRequestHandler<SendInvoiceToGIBCommand, SendInvoiceToGIBResponse>
{
    private readonly ApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly IUBLXMLGenerator _ublXmlGenerator;
    private readonly IGIBService _gibService;
    private readonly IEventBus _eventBus;
    private readonly ILogger<SendInvoiceToGIBCommandHandler> _logger;

    public SendInvoiceToGIBCommandHandler(
        ApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor,
        IUBLXMLGenerator ublXmlGenerator,
        IGIBService gibService,
        IEventBus eventBus,
        ILogger<SendInvoiceToGIBCommandHandler> logger)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
        _ublXmlGenerator = ublXmlGenerator;
        _gibService = gibService;
        _eventBus = eventBus;
        _logger = logger;
    }

    public async Task<SendInvoiceToGIBResponse> Handle(SendInvoiceToGIBCommand request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        // Invoice'ı bul
        var invoice = await _dbContext.Invoices
            .Include(i => i.Items)
            .FirstOrDefaultAsync(i => i.Id == request.InvoiceId && i.TenantId == tenantId, cancellationToken);

        if (invoice == null)
        {
            throw new NotFoundException("Fatura", request.InvoiceId);
        }

        // Zaten gönderilmiş mi?
        if (invoice.Status == "Sent" && !string.IsNullOrEmpty(invoice.GIBInvoiceId))
        {
            return new SendInvoiceToGIBResponse
            {
                InvoiceId = invoice.Id,
                InvoiceNumber = invoice.InvoiceNumber,
                Success = true,
                GIBInvoiceId = invoice.GIBInvoiceId,
                GIBInvoiceNumber = invoice.GIBInvoiceNumber,
                Message = "Bu fatura zaten GİB'e gönderilmiş"
            };
        }

        // İptal edilmiş mi?
        if (invoice.IsCancelled || invoice.Status == "Cancelled")
        {
            throw new BadRequestException("İptal edilmiş faturalar GİB'e gönderilemez");
        }

        // Tenant Invoice Settings
        var invoiceSettings = await _dbContext.TenantInvoiceSettings
            .FirstOrDefaultAsync(s => s.TenantId == tenantId, cancellationToken);

        if (invoiceSettings == null)
        {
            throw new BadRequestException("Fatura ayarları yapılandırılmamış");
        }

        if (!invoiceSettings.IsEFaturaUser)
        {
            throw new BadRequestException("E-fatura kullanıcısı değilsiniz");
        }

        // UBL XML ve imzalama kontrolü
        if (string.IsNullOrEmpty(invoice.UBLXMLSigned))
        {
            // UBL XML oluştur (eğer yoksa)
            if (string.IsNullOrEmpty(invoice.UBLXML))
            {
                var ublXml = await _ublXmlGenerator.GenerateInvoiceXMLAsync(invoice, invoiceSettings, cancellationToken);
                invoice.UBLXML = ublXml;
            }

            // İmzala
            var signedXml = await _ublXmlGenerator.SignUBLXMLAsync(invoice.UBLXML!, invoiceSettings, cancellationToken);
            invoice.UBLXMLSigned = signedXml;
            invoice.Status = "ReadyToSend";

            await _dbContext.SaveChangesAsync(cancellationToken);
        }

        // GİB'e gönder
        try
        {
            var gibResponse = await _gibService.SendInvoiceAsync(invoice.UBLXMLSigned!, invoiceSettings, cancellationToken);

            if (gibResponse.Success)
            {
                invoice.GIBInvoiceId = gibResponse.InvoiceId;
                invoice.GIBInvoiceNumber = gibResponse.InvoiceNumber;
                invoice.GIBSentAt = DateTime.UtcNow;
                invoice.Status = "Sent";
                invoice.GIBApprovalStatus = "Gönderildi";

                await _dbContext.SaveChangesAsync(cancellationToken);

                _logger.LogInformation("Invoice sent to GİB successfully: {InvoiceNumber}, GIB ID: {GIBInvoiceId}",
                    invoice.InvoiceNumber, gibResponse.InvoiceId);

                // Event publish
                await _eventBus.PublishAsync(new InvoiceSentToGIBEvent
                {
                    InvoiceId = invoice.Id,
                    TenantId = tenantId,
                    InvoiceNumber = invoice.InvoiceNumber,
                    GIBInvoiceId = gibResponse.InvoiceId
                }, cancellationToken);

                return new SendInvoiceToGIBResponse
                {
                    InvoiceId = invoice.Id,
                    InvoiceNumber = invoice.InvoiceNumber,
                    Success = true,
                    GIBInvoiceId = gibResponse.InvoiceId,
                    GIBInvoiceNumber = gibResponse.InvoiceNumber,
                    Message = "Fatura başarıyla GİB'e gönderildi"
                };
            }
            else
            {
                invoice.Status = "SendFailed";
                invoice.StatusMessage = gibResponse.ErrorMessage;
                await _dbContext.SaveChangesAsync(cancellationToken);

                _logger.LogWarning("GİB send failed for invoice {InvoiceNumber}: {Error}",
                    invoice.InvoiceNumber, gibResponse.ErrorMessage);

                return new SendInvoiceToGIBResponse
                {
                    InvoiceId = invoice.Id,
                    InvoiceNumber = invoice.InvoiceNumber,
                    Success = false,
                    ErrorMessage = gibResponse.ErrorMessage,
                    Message = $"GİB'e gönderim başarısız: {gibResponse.ErrorMessage}"
                };
            }
        }
        catch (Exception ex)
        {
            invoice.Status = "SendFailed";
            invoice.StatusMessage = ex.Message;
            await _dbContext.SaveChangesAsync(cancellationToken);

            _logger.LogError(ex, "Error sending invoice to GİB: {InvoiceNumber}", invoice.InvoiceNumber);

            return new SendInvoiceToGIBResponse
            {
                InvoiceId = invoice.Id,
                InvoiceNumber = invoice.InvoiceNumber,
                Success = false,
                ErrorMessage = ex.Message,
                Message = $"GİB'e gönderim hatası: {ex.Message}"
            };
        }
    }
}

