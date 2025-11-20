using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Application.Common.Interfaces;
using Tinisoft.Shared.Contracts;
using Finbuckle.MultiTenant;
using Tinisoft.Application.Notifications.Services;
using System.Net.Mail;
using System.Net;

namespace Tinisoft.Application.Notifications.Commands.SendEmail;

public class SendEmailCommandHandler : IRequestHandler<SendEmailCommand, SendEmailResponse>
{
    private readonly IApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly IEmailService _emailService;
    private readonly ILogger<SendEmailCommandHandler> _logger;

    public SendEmailCommandHandler(
        IApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor,
        IEmailService emailService,
        ILogger<SendEmailCommandHandler> logger)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
        _emailService = emailService;
        _logger = logger;
    }

    public async Task<SendEmailResponse> Handle(SendEmailCommand request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        // Varsayılan email provider'ı bul
        var emailProvider = await _dbContext.EmailProviders
            .FirstOrDefaultAsync(ep => 
                ep.TenantId == tenantId && 
                ep.IsActive && 
                ep.IsDefault, cancellationToken);

        if (emailProvider == null)
        {
            return new SendEmailResponse
            {
                Success = false,
                ErrorMessage = "Varsayılan email provider bulunamadı"
            };
        }

        // EmailTemplate varsa içeriği al
        string subject = request.Subject;
        string bodyHtml = request.BodyHtml;
        string? bodyText = request.BodyText;

        if (request.EmailTemplateId.HasValue)
        {
            var template = await _dbContext.EmailTemplates
                .AsNoTracking()
                .FirstOrDefaultAsync(et => 
                    et.Id == request.EmailTemplateId.Value && 
                    et.TenantId == tenantId && 
                    et.IsActive, cancellationToken);

            if (template != null)
            {
                subject = template.Subject;
                bodyHtml = template.BodyHtml;
                bodyText = template.BodyText;
            }
        }

        // EmailNotification kaydı oluştur
        var emailNotification = new Domain.Entities.EmailNotification
        {
            TenantId = tenantId,
            EmailProviderId = emailProvider.Id,
            EmailTemplateId = request.EmailTemplateId,
            ToEmail = request.ToEmail,
            ToName = request.ToName,
            CcEmail = request.CcEmail,
            BccEmail = request.BccEmail,
            Subject = subject,
            BodyHtml = bodyHtml,
            BodyText = bodyText,
            Status = "Pending",
            ReferenceId = request.ReferenceId,
            ReferenceType = request.ReferenceType
        };

        _dbContext.EmailNotifications.Add(emailNotification);
        await _dbContext.SaveChangesAsync(cancellationToken);

        // Email gönder
        try
        {
            var result = await _emailService.SendEmailAsync(emailProvider, emailNotification, cancellationToken);

            if (result.Success)
            {
                emailNotification.Status = "Sent";
                emailNotification.SentAt = DateTime.UtcNow;
                emailNotification.ProviderResponseJson = result.ProviderResponseJson;
            }
            else
            {
                emailNotification.Status = "Failed";
                emailNotification.ErrorMessage = result.ErrorMessage;
            }

            await _dbContext.SaveChangesAsync(cancellationToken);

            _logger.LogInformation("Email sent: {ToEmail}, Status: {Status}", 
                request.ToEmail, emailNotification.Status);

            return new SendEmailResponse
            {
                EmailNotificationId = emailNotification.Id,
                Success = result.Success,
                ErrorMessage = result.ErrorMessage
            };
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error sending email to {ToEmail}", request.ToEmail);
            
            emailNotification.Status = "Failed";
            emailNotification.ErrorMessage = ex.Message;
            await _dbContext.SaveChangesAsync(cancellationToken);

            return new SendEmailResponse
            {
                EmailNotificationId = emailNotification.Id,
                Success = false,
                ErrorMessage = ex.Message
            };
        }
    }
}



