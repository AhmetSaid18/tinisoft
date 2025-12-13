using MediatR;
using Microsoft.EntityFrameworkCore;
using Finbuckle.MultiTenant;
using Tinisoft.Application.Common.Interfaces;
using Tinisoft.Domain.Entities;

namespace Tinisoft.Application.Tenant.Commands.AddCustomDomain;

public class AddCustomDomainCommandHandler : IRequestHandler<AddCustomDomainCommand, AddCustomDomainResponse>
{
    private readonly IApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly ILogger<AddCustomDomainCommandHandler> _logger;

    public AddCustomDomainCommandHandler(
        IApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor,
        ILogger<AddCustomDomainCommandHandler> logger)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
        _logger = logger;
    }

    public async Task<AddCustomDomainResponse> Handle(AddCustomDomainCommand request, CancellationToken cancellationToken)
    {
        try
        {
            var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

            // Tenant'ı bul
            var tenant = await _dbContext.Tenants
                .Include(t => t.Plan)
                .Include(t => t.Domains)
                .FirstOrDefaultAsync(t => t.Id == tenantId, cancellationToken);

            if (tenant == null)
            {
                return new AddCustomDomainResponse
                {
                    Success = false,
                    ErrorMessage = "Tenant not found"
                };
            }

            // Plan kontrolü - Custom domain izni var mı?
            if (tenant.Plan != null && !tenant.Plan.CustomDomainEnabled)
            {
                return new AddCustomDomainResponse
                {
                    Success = false,
                    ErrorMessage = "Your plan does not include custom domain feature. Please upgrade your plan."
                };
            }

            // Domain zaten var mı kontrol et
            var existingDomain = await _dbContext.Domains
                .FirstOrDefaultAsync(d => d.Host == request.Host.ToLower(), cancellationToken);

            if (existingDomain != null)
            {
                return new AddCustomDomainResponse
                {
                    Success = false,
                    ErrorMessage = "This domain is already registered"
                };
            }

            // Verification token oluştur
            var verificationToken = $"tinisoft-verify={Guid.NewGuid():N}";

            // Domain oluştur
            var domain = new Tinisoft.Domain.Entities.Domain
            {
                TenantId = tenantId,
                Host = request.Host.ToLower().Trim(),
                IsPrimary = request.IsPrimary,
                IsVerified = false,
                VerificationToken = verificationToken,
                SslEnabled = false
            };

            _dbContext.Domains.Add(domain);
            await _dbContext.SaveChangesAsync(cancellationToken);

            _logger.LogInformation("Domain {Host} added for tenant {TenantId}, pending verification", 
                request.Host, tenantId);

            // DNS talimatları oluştur
            var subdomain = tenant.Slug;
            var instructions = new DnsInstructions
            {
                TxtRecord = new TxtRecordInstruction
                {
                    Type = "TXT",
                    Name = "_tinisoft-verification",
                    Value = verificationToken,
                    Ttl = 3600
                },
                CnameRecord = new CnameRecordInstruction
                {
                    Type = "CNAME",
                    Name = GetCnameRecordName(request.Host),
                    Value = $"{subdomain}.domains.tinisoft.com",
                    Ttl = 3600
                }
            };

            return new AddCustomDomainResponse
            {
                DomainId = domain.Id,
                Host = domain.Host,
                Status = "pending_verification",
                VerificationToken = verificationToken,
                Instructions = instructions,
                Success = true
            };
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error adding custom domain {Host}", request.Host);
            return new AddCustomDomainResponse
            {
                Success = false,
                ErrorMessage = $"Error adding domain: {ex.Message}"
            };
        }
    }

    private string GetCnameRecordName(string host)
    {
        // www.ornekmagaza.com → "www"
        // ornekmagaza.com → "@" (root domain)
        var parts = host.Split('.');
        if (parts.Length > 2 && parts[0].ToLower() != "www")
        {
            return parts[0];  // subdomain
        }
        else if (parts[0].ToLower() == "www")
        {
            return "www";
        }
        return "@";  // root domain
    }
}

