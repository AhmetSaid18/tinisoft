using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Application.Common.Interfaces;
using Tinisoft.Shared.Contracts;
using Tinisoft.Application.Common.Exceptions;
using Finbuckle.MultiTenant;
using Tinisoft.Shared.Events;
using Tinisoft.Shared.Contracts;
using Tinisoft.Application.Invoices.Services;

namespace Tinisoft.Application.Invoices.Commands.CancelInvoice;

public class CancelInvoiceCommandHandler : IRequestHandler<CancelInvoiceCommand, CancelInvoiceResponse>
{
    private readonly IApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly IInvoiceNumberGenerator _invoiceNumberGenerator;
    private readonly IUBLXMLGenerator _ublXmlGenerator;
    private readonly IGIBService _gibService;
    private readonly IEventBus _eventBus;
    private readonly ILogger<CancelInvoiceCommandHandler> _logger;

    public CancelInvoiceCommandHandler(
        IApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor,
        IInvoiceNumberGenerator invoiceNumberGenerator,
        IUBLXMLGenerator ublXmlGenerator,
        IGIBService gibService,
        IEventBus eventBus,
        ILogger<CancelInvoiceCommandHandler> logger)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
        _invoiceNumberGenerator = invoiceNumberGenerator;
        _ublXmlGenerator = ublXmlGenerator;
        _gibService = gibService;
        _eventBus = eventBus;
        _logger = logger;
    }

    public async Task<CancelInvoiceResponse> Handle(CancelInvoiceCommand request, CancellationToken cancellationToken)
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

        // İptal edilebilir mi kontrol et
        if (invoice.IsCancelled)
        {
            throw new BadRequestException("Bu fatura zaten iptal edilmiş");
        }

        if (invoice.Status == "Cancelled")
        {
            throw new BadRequestException("Bu fatura zaten iptal edilmiş");
        }

        // GİB'e gönderilmişse, GİB'den de iptal etmek gerekir
        if (!string.IsNullOrEmpty(invoice.GIBInvoiceId) && invoice.Status == "Sent")
        {
            // GİB'den iptal işlemi yapılmalı (şimdilik sadece local iptal)
            _logger.LogWarning("Invoice {InvoiceNumber} was sent to GİB, cancellation should be done through GİB", 
                invoice.InvoiceNumber);
        }

        // Invoice'ı iptal et
        invoice.IsCancelled = true;
        invoice.Status = "Cancelled";
        invoice.CancelledAt = DateTime.UtcNow;
        invoice.CancellationReason = request.CancellationReason;

        // İptal faturası oluştur (eğer istenirse)
        string? cancellationInvoiceNumber = null;
        if (request.CreateCancellationInvoice)
        {
            var invoiceSettings = await _dbContext.TenantInvoiceSettings
                .FirstOrDefaultAsync(s => s.TenantId == tenantId, cancellationToken);

            if (invoiceSettings != null)
            {
                // İptal faturası numarası oluştur
                var cancelInvoiceNumber = await _invoiceNumberGenerator.GenerateNextInvoiceNumberAsync(
                    tenantId,
                    invoiceSettings.InvoicePrefix,
                    invoiceSettings.InvoiceSerial,
                    cancellationToken);

                cancellationInvoiceNumber = cancelInvoiceNumber.FullNumber;
                invoice.CancellationInvoiceNumber = cancellationInvoiceNumber;

                _logger.LogInformation("Cancellation invoice number created: {CancellationInvoiceNumber} for Invoice: {InvoiceNumber}",
                    cancellationInvoiceNumber, invoice.InvoiceNumber);
            }
        }

        await _dbContext.SaveChangesAsync(cancellationToken);

        _logger.LogInformation("Invoice cancelled: {InvoiceNumber}, Reason: {Reason}", 
            invoice.InvoiceNumber, request.CancellationReason);

        // Event publish
        await _eventBus.PublishAsync(new InvoiceCancelledEvent
        {
            InvoiceId = invoice.Id,
            TenantId = tenantId,
            InvoiceNumber = invoice.InvoiceNumber,
            CancellationReason = request.CancellationReason
        }, cancellationToken);

        return new CancelInvoiceResponse
        {
            InvoiceId = invoice.Id,
            InvoiceNumber = invoice.InvoiceNumber,
            Status = invoice.Status,
            CancellationInvoiceNumber = cancellationInvoiceNumber,
            Message = "Fatura başarıyla iptal edildi"
        };
    }
}



