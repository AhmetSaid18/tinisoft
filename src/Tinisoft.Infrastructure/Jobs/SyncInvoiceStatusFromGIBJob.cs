using Hangfire;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Tinisoft.Infrastructure.Persistence;
using Tinisoft.Application.Invoices.Services;
using Tinisoft.Shared.Events;
using Tinisoft.Shared.Contracts;

namespace Tinisoft.Infrastructure.Jobs;

/// <summary>
/// GİB'den fatura durumlarını senkronize eden background job
/// Periyodik olarak GİB'e gönderilmiş faturaların durumunu kontrol eder
/// </summary>
public class SyncInvoiceStatusFromGIBJob
{
    private readonly IServiceProvider _serviceProvider;
    private readonly ILogger<SyncInvoiceStatusFromGIBJob> _logger;

    public SyncInvoiceStatusFromGIBJob(
        IServiceProvider serviceProvider,
        ILogger<SyncInvoiceStatusFromGIBJob> logger)
    {
        _serviceProvider = serviceProvider;
        _logger = logger;
    }

    [AutomaticRetry(Attempts = 3, DelaysInSeconds = new[] { 60, 120, 300 })]
    public async Task ExecuteAsync(CancellationToken cancellationToken = default)
    {
        _logger.LogInformation("Starting invoice status sync from GİB");

        using var scope = _serviceProvider.CreateScope();
        var dbContext = scope.ServiceProvider.GetRequiredService<ApplicationDbContext>();
        var gibService = scope.ServiceProvider.GetRequiredService<IGIBService>();
        var eventBus = scope.ServiceProvider.GetRequiredService<IEventBus>();

        try
        {
            // Son 24 saat içinde GİB'e gönderilmiş ve henüz onaylanmamış/reddedilmemiş faturaları bul
            var cutoffDate = DateTime.UtcNow.AddHours(-24);
            
            var invoices = await dbContext.Invoices
                .Include(i => i.Tenant)
                .Where(i => 
                    !string.IsNullOrEmpty(i.GIBInvoiceId) &&
                    i.GIBSentAt.HasValue &&
                    i.GIBSentAt >= cutoffDate &&
                    i.Status != "Approved" &&
                    i.Status != "Rejected" &&
                    i.Status != "Cancelled")
                .ToListAsync(cancellationToken);

            _logger.LogInformation("Found {Count} invoices to sync status from GİB", invoices.Count);

            foreach (var invoice in invoices)
            {
                try
                {
                    // Tenant invoice settings al
                    var invoiceSettings = await dbContext.TenantInvoiceSettings
                        .FirstOrDefaultAsync(s => s.TenantId == invoice.TenantId, cancellationToken);

                    if (invoiceSettings == null || !invoiceSettings.IsEFaturaUser)
                    {
                        continue;
                    }

                    // GİB'den durum sorgula
                    var gibResponse = await gibService.GetInvoiceStatusAsync(
                        invoice.GIBInvoiceId!,
                        invoiceSettings,
                        cancellationToken);

                    if (gibResponse.Success)
                    {
                        var oldStatus = invoice.Status;
                        var oldApprovalStatus = invoice.GIBApprovalStatus;

                        // Durum güncelle
                        invoice.GIBApprovalStatus = gibResponse.Status;
                        invoice.StatusMessage = gibResponse.StatusMessage;

                        if (gibResponse.Status == "Onaylandı" && invoice.Status != "Approved")
                        {
                            invoice.Status = "Approved";
                            if (gibResponse.ProcessedAt.HasValue)
                            {
                                invoice.GIBApprovedAt = gibResponse.ProcessedAt.Value;
                            }

                            // Event publish
                            await eventBus.PublishAsync(new InvoiceApprovedByGIBEvent
                            {
                                InvoiceId = invoice.Id,
                                TenantId = invoice.TenantId,
                                InvoiceNumber = invoice.InvoiceNumber,
                                GIBInvoiceId = invoice.GIBInvoiceId!
                            }, cancellationToken);

                            _logger.LogInformation("Invoice approved by GİB: {InvoiceNumber}", invoice.InvoiceNumber);
                        }
                        else if (gibResponse.Status == "Reddedildi" && invoice.Status != "Rejected")
                        {
                            invoice.Status = "Rejected";

                            _logger.LogWarning("Invoice rejected by GİB: {InvoiceNumber}, Reason: {Reason}",
                                invoice.InvoiceNumber, gibResponse.StatusMessage);
                        }

                        // Durum değiştiyse kaydet
                        if (oldStatus != invoice.Status || oldApprovalStatus != invoice.GIBApprovalStatus)
                        {
                            await dbContext.SaveChangesAsync(cancellationToken);

                            _logger.LogInformation("Invoice status updated from GİB: {InvoiceNumber}, Old: {OldStatus}, New: {NewStatus}",
                                invoice.InvoiceNumber, oldStatus, invoice.Status);
                        }
                    }
                }
                catch (Exception ex)
                {
                    _logger.LogError(ex, "Error syncing invoice status from GİB: {InvoiceNumber}", invoice.InvoiceNumber);
                    // Devam et, diğer faturaları işle
                }
            }

            _logger.LogInformation("Completed invoice status sync from GİB");
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error in invoice status sync job");
            throw;
        }
    }
}

