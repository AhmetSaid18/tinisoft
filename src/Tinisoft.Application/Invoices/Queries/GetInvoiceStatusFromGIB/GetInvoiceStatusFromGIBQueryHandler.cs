using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Application.Common.Interfaces;
using Tinisoft.Shared.Contracts;
using Tinisoft.Application.Common.Exceptions;
using Finbuckle.MultiTenant;
using Tinisoft.Application.Invoices.Services;

namespace Tinisoft.Application.Invoices.Queries.GetInvoiceStatusFromGIB;

public class GetInvoiceStatusFromGIBQueryHandler : IRequestHandler<GetInvoiceStatusFromGIBQuery, GetInvoiceStatusFromGIBResponse>
{
    private readonly IApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly IGIBService _gibService;
    private readonly ILogger<GetInvoiceStatusFromGIBQueryHandler> _logger;

    public GetInvoiceStatusFromGIBQueryHandler(
        IApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor,
        IGIBService gibService,
        ILogger<GetInvoiceStatusFromGIBQueryHandler> logger)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
        _gibService = gibService;
        _logger = logger;
    }

    public async Task<GetInvoiceStatusFromGIBResponse> Handle(GetInvoiceStatusFromGIBQuery request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        // Invoice'ı bul
        var invoice = await _dbContext.Invoices
            .FirstOrDefaultAsync(i => i.Id == request.InvoiceId && i.TenantId == tenantId, cancellationToken);

        if (invoice == null)
        {
            throw new NotFoundException("Fatura", request.InvoiceId);
        }

        // GİB'e gönderilmiş mi?
        if (string.IsNullOrEmpty(invoice.GIBInvoiceId))
        {
            return new GetInvoiceStatusFromGIBResponse
            {
                InvoiceId = invoice.Id,
                InvoiceNumber = invoice.InvoiceNumber,
                Success = false,
                Status = invoice.Status,
                StatusMessage = "Bu fatura henüz GİB'e gönderilmemiş"
            };
        }

        // Tenant Invoice Settings
        var invoiceSettings = await _dbContext.TenantInvoiceSettings
            .FirstOrDefaultAsync(s => s.TenantId == tenantId, cancellationToken);

        if (invoiceSettings == null)
        {
            throw new BadRequestException("Fatura ayarları yapılandırılmamış");
        }

        // GİB'den durum sorgula
        try
        {
            var gibResponse = await _gibService.GetInvoiceStatusAsync(invoice.GIBInvoiceId, invoiceSettings, cancellationToken);

            // GİB'den gelen durumu invoice'a kaydet
            if (gibResponse.Success && !string.IsNullOrEmpty(gibResponse.Status))
            {
                invoice.GIBApprovalStatus = gibResponse.Status;
                invoice.StatusMessage = gibResponse.StatusMessage;

                if (gibResponse.Status == "Onaylandı")
                {
                    invoice.Status = "Approved";
                    if (gibResponse.ProcessedAt.HasValue && !invoice.GIBApprovedAt.HasValue)
                    {
                        invoice.GIBApprovedAt = gibResponse.ProcessedAt.Value;
                    }
                }
                else if (gibResponse.Status == "Reddedildi")
                {
                    invoice.Status = "Rejected";
                }

                await _dbContext.SaveChangesAsync(cancellationToken);

                _logger.LogInformation("Invoice status synced from GİB: {InvoiceNumber}, Status: {Status}",
                    invoice.InvoiceNumber, gibResponse.Status);
            }

            return new GetInvoiceStatusFromGIBResponse
            {
                InvoiceId = invoice.Id,
                InvoiceNumber = invoice.InvoiceNumber,
                Success = gibResponse.Success,
                Status = gibResponse.Status,
                StatusMessage = gibResponse.StatusMessage,
                ProcessedAt = gibResponse.ProcessedAt,
                GIBInvoiceId = invoice.GIBInvoiceId
            };
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting invoice status from GİB: {InvoiceNumber}", invoice.InvoiceNumber);
            return new GetInvoiceStatusFromGIBResponse
            {
                InvoiceId = invoice.Id,
                InvoiceNumber = invoice.InvoiceNumber,
                Success = false,
                Status = invoice.Status,
                StatusMessage = $"GİB'den durum sorgulama hatası: {ex.Message}",
                GIBInvoiceId = invoice.GIBInvoiceId
            };
        }
    }
}



