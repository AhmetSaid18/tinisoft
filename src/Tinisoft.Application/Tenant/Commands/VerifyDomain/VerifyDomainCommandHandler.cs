using MediatR;
using Microsoft.EntityFrameworkCore;
using Finbuckle.MultiTenant;
using Tinisoft.Application.Common.Interfaces;

namespace Tinisoft.Application.Tenant.Commands.VerifyDomain;

public class VerifyDomainCommandHandler : IRequestHandler<VerifyDomainCommand, VerifyDomainResponse>
{
    private readonly IApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly IDnsVerificationService _dnsVerificationService;
    private readonly ITraefikDomainService _traefikDomainService;
    private readonly ILogger<VerifyDomainCommandHandler> _logger;

    public VerifyDomainCommandHandler(
        IApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor,
        IDnsVerificationService dnsVerificationService,
        ITraefikDomainService traefikDomainService,
        ILogger<VerifyDomainCommandHandler> logger)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
        _dnsVerificationService = dnsVerificationService;
        _traefikDomainService = traefikDomainService;
        _logger = logger;
    }

    public async Task<VerifyDomainResponse> Handle(VerifyDomainCommand request, CancellationToken cancellationToken)
    {
        try
        {
            var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

            // Domain'i bul
            var domain = await _dbContext.Domains
                .Include(d => d.Tenant)
                .FirstOrDefaultAsync(d => d.Id == request.DomainId && d.TenantId == tenantId, cancellationToken);

            if (domain == null)
            {
                return new VerifyDomainResponse
                {
                    Success = false,
                    Message = "Domain not found"
                };
            }

            // Zaten verify edilmiş mi?
            if (domain.IsVerified)
            {
                return new VerifyDomainResponse
                {
                    Success = true,
                    Message = "Domain is already verified",
                    Host = domain.Host,
                    Status = "verified",
                    SslEnabled = domain.SslEnabled
                };
            }

            // CNAME target oluştur
            var cnameTarget = $"{domain.Tenant!.Slug}.domains.tinisoft.com";

            // DNS verification yap
            var verificationResult = await _dnsVerificationService.FullVerificationAsync(
                domain.Host,
                domain.VerificationToken!,
                cnameTarget,
                cancellationToken);

            if (!verificationResult.FullyVerified)
            {
                return new VerifyDomainResponse
                {
                    Success = false,
                    Message = string.Join("; ", verificationResult.Errors),
                    Host = domain.Host,
                    Status = "pending_verification"
                };
            }

            // Verification başarılı!
            domain.IsVerified = true;
            domain.VerifiedAt = DateTime.UtcNow;

            // Traefik'e domain ekle
            await _traefikDomainService.AddDomainAsync(domain.Host, cancellationToken);

            // SSL otomatik aktif olacak (Traefik + Let's Encrypt)
            domain.SslEnabled = true;
            domain.SslIssuedAt = DateTime.UtcNow;
            domain.SslExpiresAt = DateTime.UtcNow.AddDays(90);  // Let's Encrypt 90 gün

            await _dbContext.SaveChangesAsync(cancellationToken);

            _logger.LogInformation("Domain {Host} verified and activated for tenant {TenantId}", 
                domain.Host, tenantId);

            return new VerifyDomainResponse
            {
                Success = true,
                Message = "Domain verified successfully! Your domain will be active within 1-2 minutes.",
                Host = domain.Host,
                Status = "active",
                SslEnabled = true
            };
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error verifying domain {DomainId}", request.DomainId);
            return new VerifyDomainResponse
            {
                Success = false,
                Message = $"Error verifying domain: {ex.Message}"
            };
        }
    }
}

