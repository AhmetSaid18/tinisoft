using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Infrastructure.Persistence;
using Tinisoft.Application.Common.Exceptions;
using Finbuckle.MultiTenant;
using System.Security.Cryptography.X509Certificates;

namespace Tinisoft.Application.Invoices.Commands.UpdateInvoiceSettings;

public class UpdateInvoiceSettingsCommandHandler : IRequestHandler<UpdateInvoiceSettingsCommand, UpdateInvoiceSettingsResponse>
{
    private readonly ApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly ILogger<UpdateInvoiceSettingsCommandHandler> _logger;

    public UpdateInvoiceSettingsCommandHandler(
        ApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor,
        ILogger<UpdateInvoiceSettingsCommandHandler> logger)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
        _logger = logger;
    }

    public async Task<UpdateInvoiceSettingsResponse> Handle(UpdateInvoiceSettingsCommand request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        // Mevcut ayarları bul veya oluştur
        var settings = await _dbContext.TenantInvoiceSettings
            .FirstOrDefaultAsync(s => s.TenantId == tenantId, cancellationToken);

        if (settings == null)
        {
            settings = new Domain.Entities.TenantInvoiceSettings
            {
                TenantId = tenantId,
                Id = Guid.NewGuid(),
                CreatedAt = DateTime.UtcNow
            };
            _dbContext.TenantInvoiceSettings.Add(settings);
        }

        // E-Fatura User Info
        if (request.IsEFaturaUser.HasValue)
            settings.IsEFaturaUser = request.IsEFaturaUser.Value;
        if (request.VKN != null)
            settings.VKN = request.VKN;
        if (request.TCKN != null)
            settings.TCKN = request.TCKN;
        if (request.TaxOffice != null)
            settings.TaxOffice = request.TaxOffice;
        if (request.TaxNumber != null)
            settings.TaxNumber = request.TaxNumber;
        if (request.EFaturaAlias != null)
            settings.EFaturaAlias = request.EFaturaAlias;
        if (request.EFaturaPassword != null)
            settings.EFaturaPassword = request.EFaturaPassword; // TODO: Encrypt

        // Company Info
        if (request.CompanyName != null)
            settings.CompanyName = request.CompanyName;
        if (request.CompanyTitle != null)
            settings.CompanyTitle = request.CompanyTitle;
        if (request.CompanyAddressLine1 != null)
            settings.CompanyAddressLine1 = request.CompanyAddressLine1;
        if (request.CompanyAddressLine2 != null)
            settings.CompanyAddressLine2 = request.CompanyAddressLine2;
        if (request.CompanyCity != null)
            settings.CompanyCity = request.CompanyCity;
        if (request.CompanyState != null)
            settings.CompanyState = request.CompanyState;
        if (request.CompanyPostalCode != null)
            settings.CompanyPostalCode = request.CompanyPostalCode;
        if (request.CompanyCountry != null)
            settings.CompanyCountry = request.CompanyCountry;
        if (request.CompanyPhone != null)
            settings.CompanyPhone = request.CompanyPhone;
        if (request.CompanyEmail != null)
            settings.CompanyEmail = request.CompanyEmail;
        if (request.CompanyWebsite != null)
            settings.CompanyWebsite = request.CompanyWebsite;

        // Bank Account Info
        if (request.BankName != null)
            settings.BankName = request.BankName;
        if (request.BankBranch != null)
            settings.BankBranch = request.BankBranch;
        if (request.IBAN != null)
            settings.IBAN = request.IBAN;
        if (request.AccountName != null)
            settings.AccountName = request.AccountName;

        // Mali Mühür
        if (request.MaliMuhurCertificateBase64 != null)
        {
            // Sertifikayı validate et
            try
            {
                var certificateBytes = Convert.FromBase64String(request.MaliMuhurCertificateBase64);
                var certificate = new X509Certificate2(certificateBytes, request.MaliMuhurPassword ?? string.Empty,
                    X509KeyStorageFlags.MachineKeySet | X509KeyStorageFlags.Exportable);

                settings.MaliMuhurCertificateBase64 = request.MaliMuhurCertificateBase64; // TODO: Encrypt
                settings.MaliMuhurPassword = request.MaliMuhurPassword; // TODO: Encrypt
                settings.MaliMuhurSerialNumber = certificate.SerialNumber;
                settings.MaliMuhurExpiryDate = certificate.NotAfter;

                _logger.LogInformation("Mali mühür sertifikası yüklendi: Serial={Serial}, Expiry={Expiry}",
                    certificate.SerialNumber, certificate.NotAfter);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Mali mühür sertifikası geçersiz");
                throw new BadRequestException("Mali mühür sertifikası geçersiz veya şifre yanlış");
            }
        }

        // Invoice Numbering
        if (request.InvoicePrefix != null)
            settings.InvoicePrefix = request.InvoicePrefix;
        if (request.InvoiceSerial != null)
            settings.InvoiceSerial = request.InvoiceSerial;
        if (request.InvoiceStartNumber.HasValue)
            settings.InvoiceStartNumber = request.InvoiceStartNumber.Value;

        // Invoice Settings
        if (request.DefaultInvoiceType != null)
            settings.DefaultInvoiceType = request.DefaultInvoiceType;
        if (request.DefaultProfileId != null)
            settings.DefaultProfileId = request.DefaultProfileId;
        if (request.PaymentDueDays.HasValue)
            settings.PaymentDueDays = request.PaymentDueDays.Value;

        // Auto Invoice
        if (request.AutoCreateInvoiceOnOrderPaid.HasValue)
            settings.AutoCreateInvoiceOnOrderPaid = request.AutoCreateInvoiceOnOrderPaid.Value;
        if (request.AutoSendToGIB.HasValue)
            settings.AutoSendToGIB = request.AutoSendToGIB.Value;

        // GİB Integration Settings
        if (request.UseTestEnvironment.HasValue)
            settings.UseTestEnvironment = request.UseTestEnvironment.Value;

        settings.UpdatedAt = DateTime.UtcNow;
        settings.IsActive = true;

        await _dbContext.SaveChangesAsync(cancellationToken);

        _logger.LogInformation("Invoice settings updated for Tenant: {TenantId}", tenantId);

        return new UpdateInvoiceSettingsResponse
        {
            TenantId = tenantId,
            IsEFaturaUser = settings.IsEFaturaUser,
            VKN = settings.VKN,
            Message = "Fatura ayarları başarıyla güncellendi"
        };
    }
}

