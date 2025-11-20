using Microsoft.EntityFrameworkCore;
using Tinisoft.Infrastructure.Persistence;
using Tinisoft.Application.Invoices.Services;
using Microsoft.Extensions.Logging;

namespace Tinisoft.Infrastructure.Services;

public class InvoiceNumberGenerator : IInvoiceNumberGenerator
{
    private readonly ApplicationDbContext _dbContext;
    private readonly ILogger<InvoiceNumberGenerator> _logger;

    public InvoiceNumberGenerator(
        ApplicationDbContext dbContext,
        ILogger<InvoiceNumberGenerator> logger)
    {
        _dbContext = dbContext;
        _logger = logger;
    }

    public async Task<InvoiceNumberResult> GenerateNextInvoiceNumberAsync(
        Guid tenantId,
        string prefix,
        string serial,
        CancellationToken cancellationToken)
    {
        // Tenant Invoice Settings'den son numarayı al ve artır
        var settings = await _dbContext.TenantInvoiceSettings
            .FirstOrDefaultAsync(s => s.TenantId == tenantId, cancellationToken);

        if (settings == null)
        {
            throw new InvalidOperationException($"Invoice settings not found for tenant: {tenantId}");
        }

        // Son numarayı artır
        settings.LastInvoiceNumber++;
        var nextNumber = settings.LastInvoiceNumber;

        // Fatura numarasını formatla (0001, 0002, vb.)
        var formattedNumber = nextNumber.ToString().PadLeft(4, '0');

        // Full number (prefix + yıl + numara + seri)
        var currentYear = DateTime.UtcNow.Year;
        var fullNumber = $"{prefix}{currentYear}{formattedNumber}{serial}";

        await _dbContext.SaveChangesAsync(cancellationToken);

        _logger.LogInformation("Generated invoice number: {FullNumber} for Tenant: {TenantId}", 
            fullNumber, tenantId);

        return new InvoiceNumberResult
        {
            Number = nextNumber.ToString(), // Sadece numara (1, 2, 3, ...)
            Serial = serial,
            FullNumber = fullNumber // Tam format: FT20240001A
        };
    }
}

