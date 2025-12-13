using Hangfire;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;
using Tinisoft.Infrastructure.Persistence;
using Tinisoft.Infrastructure.Services;
using Tinisoft.Application.Common.Interfaces;

namespace Tinisoft.Infrastructure.Jobs;

/// <summary>
/// Domain verification background job
/// Her 5 dakikada bir pending domain'leri kontrol eder ve otomatik verify eder
/// </summary>
public class DomainVerificationJob
{
    private readonly ApplicationDbContext _dbContext;
    private readonly IDnsVerificationService _dnsVerificationService;
    private readonly ITraefikDomainService _traefikDomainService;
    private readonly ILogger<DomainVerificationJob> _logger;

    public DomainVerificationJob(
        ApplicationDbContext dbContext,
        IDnsVerificationService dnsVerificationService,
        ITraefikDomainService traefikDomainService,
        ILogger<DomainVerificationJob> logger)
    {
        _dbContext = dbContext;
        _dnsVerificationService = dnsVerificationService;
        _traefikDomainService = traefikDomainService;
        _logger = logger;
    }

    /// <summary>
    /// Pending domain'leri kontrol et ve verify et
    /// </summary>
    [AutomaticRetry(Attempts = 2, DelaysInSeconds = new[] { 60, 300 })]
    public async Task ExecuteAsync(CancellationToken cancellationToken = default)
    {
        try
        {
            _logger.LogInformation("Starting domain verification job");

            // Verify edilmemiş domain'leri bul
            var pendingDomains = await _dbContext.Domains
                .Include(d => d.Tenant)
                .Where(d => !d.IsVerified && d.VerificationToken != null)
                .ToListAsync(cancellationToken);

            if (pendingDomains.Count == 0)
            {
                _logger.LogInformation("No pending domains found for verification");
                return;
            }

            _logger.LogInformation("Found {Count} pending domains for verification", pendingDomains.Count);

            var verifiedCount = 0;
            var failedCount = 0;

            foreach (var domain in pendingDomains)
            {
                try
                {
                    var cnameTarget = $"{domain.Tenant!.Slug}.domains.tinisoft.com";

                    // DNS verification yap
                    var verificationResult = await _dnsVerificationService.FullVerificationAsync(
                        domain.Host,
                        domain.VerificationToken!,
                        cnameTarget,
                        cancellationToken);

                    if (verificationResult.FullyVerified)
                    {
                        // Verification başarılı!
                        domain.IsVerified = true;
                        domain.VerifiedAt = DateTime.UtcNow;

                        // Traefik'e domain ekle
                        await _traefikDomainService.AddDomainAsync(domain.Host, cancellationToken);

                        // SSL aktif et
                        domain.SslEnabled = true;
                        domain.SslIssuedAt = DateTime.UtcNow;
                        domain.SslExpiresAt = DateTime.UtcNow.AddDays(90);

                        verifiedCount++;
                        _logger.LogInformation("Domain {Host} verified successfully (auto)", domain.Host);
                    }
                    else
                    {
                        _logger.LogDebug("Domain {Host} verification pending: {Errors}", 
                            domain.Host, string.Join(", ", verificationResult.Errors));
                        failedCount++;
                    }
                }
                catch (Exception ex)
                {
                    _logger.LogError(ex, "Error verifying domain {Host}", domain.Host);
                    failedCount++;
                }
            }

            await _dbContext.SaveChangesAsync(cancellationToken);

            _logger.LogInformation(
                "Domain verification job completed. Verified: {Verified}, Pending: {Failed}",
                verifiedCount, failedCount);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error in domain verification job");
            throw;
        }
    }

    /// <summary>
    /// Belirli bir domain'i verify et (manuel trigger)
    /// </summary>
    public async Task VerifyDomainAsync(Guid domainId, CancellationToken cancellationToken = default)
    {
        var domain = await _dbContext.Domains
            .Include(d => d.Tenant)
            .FirstOrDefaultAsync(d => d.Id == domainId, cancellationToken);

        if (domain == null)
        {
            _logger.LogWarning("Domain {DomainId} not found for verification", domainId);
            return;
        }

        if (domain.IsVerified)
        {
            _logger.LogInformation("Domain {Host} is already verified", domain.Host);
            return;
        }

        var cnameTarget = $"{domain.Tenant!.Slug}.domains.tinisoft.com";

        var verificationResult = await _dnsVerificationService.FullVerificationAsync(
            domain.Host,
            domain.VerificationToken!,
            cnameTarget,
            cancellationToken);

        if (verificationResult.FullyVerified)
        {
            domain.IsVerified = true;
            domain.VerifiedAt = DateTime.UtcNow;

            await _traefikDomainService.AddDomainAsync(domain.Host, cancellationToken);

            domain.SslEnabled = true;
            domain.SslIssuedAt = DateTime.UtcNow;
            domain.SslExpiresAt = DateTime.UtcNow.AddDays(90);

            await _dbContext.SaveChangesAsync(cancellationToken);

            _logger.LogInformation("Domain {Host} verified successfully (manual)", domain.Host);
        }
        else
        {
            _logger.LogWarning("Domain {Host} verification failed: {Errors}", 
                domain.Host, string.Join(", ", verificationResult.Errors));
        }
    }
}

