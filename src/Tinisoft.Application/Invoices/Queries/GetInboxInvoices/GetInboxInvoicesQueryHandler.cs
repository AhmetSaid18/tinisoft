using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Application.Common.Interfaces;
using Tinisoft.Shared.Contracts;
using Finbuckle.MultiTenant;
using Tinisoft.Application.Invoices.Services;

namespace Tinisoft.Application.Invoices.Queries.GetInboxInvoices;

public class GetInboxInvoicesQueryHandler : IRequestHandler<GetInboxInvoicesQuery, GetInboxInvoicesResponse>
{
    private readonly IApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly IGIBService _gibService;
    private readonly ILogger<GetInboxInvoicesQueryHandler> _logger;

    public GetInboxInvoicesQueryHandler(
        IApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor,
        IGIBService gibService,
        ILogger<GetInboxInvoicesQueryHandler> logger)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
        _gibService = gibService;
        _logger = logger;
    }

    public async Task<GetInboxInvoicesResponse> Handle(GetInboxInvoicesQuery request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        // Tenant Invoice Settings
        var invoiceSettings = await _dbContext.TenantInvoiceSettings
            .FirstOrDefaultAsync(s => s.TenantId == tenantId, cancellationToken);

        if (invoiceSettings == null || !invoiceSettings.IsEFaturaUser)
        {
            return new GetInboxInvoicesResponse
            {
                Invoices = new List<InboxInvoiceDto>(),
                TotalCount = 0
            };
        }

        try
        {
            // GİB'den gelen faturaları al
            var gibInvoices = await _gibService.GetInboxInvoicesAsync(invoiceSettings, cancellationToken);

            // Filtreleme (eğer varsa)
            if (request.StartDate.HasValue)
            {
                gibInvoices = gibInvoices.Where(i => i.InvoiceDate >= request.StartDate.Value).ToList();
            }

            if (request.EndDate.HasValue)
            {
                gibInvoices = gibInvoices.Where(i => i.InvoiceDate <= request.EndDate.Value).ToList();
            }

            if (!string.IsNullOrEmpty(request.SenderVKN))
            {
                gibInvoices = gibInvoices.Where(i => i.SenderVKN == request.SenderVKN).ToList();
            }

            var invoices = gibInvoices.Select(i => new InboxInvoiceDto
            {
                InvoiceId = i.InvoiceId,
                InvoiceNumber = i.InvoiceNumber,
                InvoiceDate = i.InvoiceDate,
                SenderVKN = i.SenderVKN,
                SenderName = i.SenderName,
                Total = i.Total,
                Status = i.Status
            }).ToList();

            _logger.LogInformation("Retrieved {Count} inbox invoices from GİB for Tenant: {TenantId}",
                invoices.Count, tenantId);

            return new GetInboxInvoicesResponse
            {
                Invoices = invoices,
                TotalCount = invoices.Count
            };
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting inbox invoices from GİB for Tenant: {TenantId}", tenantId);
            return new GetInboxInvoicesResponse
            {
                Invoices = new List<InboxInvoiceDto>(),
                TotalCount = 0
            };
        }
    }
}



