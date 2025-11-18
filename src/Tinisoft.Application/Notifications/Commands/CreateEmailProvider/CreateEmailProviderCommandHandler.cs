using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Infrastructure.Persistence;
using Finbuckle.MultiTenant;

namespace Tinisoft.Application.Notifications.Commands.CreateEmailProvider;

public class CreateEmailProviderCommandHandler : IRequestHandler<CreateEmailProviderCommand, CreateEmailProviderResponse>
{
    private readonly ApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly ILogger<CreateEmailProviderCommandHandler> _logger;

    public CreateEmailProviderCommandHandler(
        ApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor,
        ILogger<CreateEmailProviderCommandHandler> logger)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
        _logger = logger;
    }

    public async Task<CreateEmailProviderResponse> Handle(CreateEmailProviderCommand request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        // Eğer default olarak işaretleniyorsa, diğer provider'ları default'tan çıkar
        if (request.IsDefault)
        {
            var defaultProviders = await _dbContext.EmailProviders
                .Where(ep => ep.TenantId == tenantId && ep.IsDefault)
                .ToListAsync(cancellationToken);

            foreach (var provider in defaultProviders)
            {
                provider.IsDefault = false;
            }
        }

        var emailProvider = new Domain.Entities.EmailProvider
        {
            TenantId = tenantId,
            ProviderName = request.ProviderName,
            SmtpHost = request.SmtpHost,
            SmtpPort = request.SmtpPort,
            EnableSsl = request.EnableSsl,
            SmtpUsername = request.SmtpUsername,
            SmtpPassword = request.SmtpPassword, // TODO: Encrypt
            FromEmail = request.FromEmail,
            FromName = request.FromName,
            ReplyToEmail = request.ReplyToEmail,
            SettingsJson = request.SettingsJson,
            IsDefault = request.IsDefault,
            IsActive = true
        };

        _dbContext.EmailProviders.Add(emailProvider);
        await _dbContext.SaveChangesAsync(cancellationToken);

        _logger.LogInformation("Email provider created: {ProviderName} for tenant {TenantId}", 
            request.ProviderName, tenantId);

        return new CreateEmailProviderResponse
        {
            EmailProviderId = emailProvider.Id,
            ProviderName = emailProvider.ProviderName
        };
    }
}

