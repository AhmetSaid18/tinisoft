using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Infrastructure.Persistence;
using Tinisoft.Application.Common.Exceptions;
using Finbuckle.MultiTenant;

namespace Tinisoft.Application.Invoices.Queries.GetInvoiceSettings;

public class GetInvoiceSettingsQueryHandler : IRequestHandler<GetInvoiceSettingsQuery, GetInvoiceSettingsResponse>
{
    private readonly ApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;

    public GetInvoiceSettingsQueryHandler(
        ApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
    }

    public async Task<GetInvoiceSettingsResponse> Handle(GetInvoiceSettingsQuery request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        var settings = await _dbContext.TenantInvoiceSettings
            .FirstOrDefaultAsync(s => s.TenantId == tenantId, cancellationToken);

        if (settings == null)
        {
            // Default settings döndür
            return new GetInvoiceSettingsResponse
            {
                TenantId = tenantId,
                IsEFaturaUser = false,
                InvoicePrefix = "FT",
                InvoiceSerial = "A",
                InvoiceStartNumber = 1,
                LastInvoiceNumber = 0,
                DefaultInvoiceType = "eFatura",
                DefaultProfileId = "TICARIFATURA",
                PaymentDueDays = 30,
                AutoCreateInvoiceOnOrderPaid = true,
                AutoSendToGIB = true,
                UseTestEnvironment = false,
                IsActive = false
            };
        }

        return new GetInvoiceSettingsResponse
        {
            TenantId = settings.TenantId,
            IsEFaturaUser = settings.IsEFaturaUser,
            VKN = settings.VKN,
            TCKN = settings.TCKN,
            TaxOffice = settings.TaxOffice,
            TaxNumber = settings.TaxNumber,
            EFaturaAlias = settings.EFaturaAlias,
            CompanyName = settings.CompanyName,
            CompanyTitle = settings.CompanyTitle,
            CompanyAddressLine1 = settings.CompanyAddressLine1,
            CompanyAddressLine2 = settings.CompanyAddressLine2,
            CompanyCity = settings.CompanyCity,
            CompanyState = settings.CompanyState,
            CompanyPostalCode = settings.CompanyPostalCode,
            CompanyCountry = settings.CompanyCountry,
            CompanyPhone = settings.CompanyPhone,
            CompanyEmail = settings.CompanyEmail,
            CompanyWebsite = settings.CompanyWebsite,
            BankName = settings.BankName,
            BankBranch = settings.BankBranch,
            IBAN = settings.IBAN,
            AccountName = settings.AccountName,
            MaliMuhurSerialNumber = settings.MaliMuhurSerialNumber,
            MaliMuhurExpiryDate = settings.MaliMuhurExpiryDate,
            HasMaliMuhur = !string.IsNullOrEmpty(settings.MaliMuhurCertificateBase64),
            InvoicePrefix = settings.InvoicePrefix,
            InvoiceSerial = settings.InvoiceSerial,
            InvoiceStartNumber = settings.InvoiceStartNumber,
            LastInvoiceNumber = settings.LastInvoiceNumber,
            DefaultInvoiceType = settings.DefaultInvoiceType,
            DefaultProfileId = settings.DefaultProfileId,
            PaymentDueDays = settings.PaymentDueDays,
            AutoCreateInvoiceOnOrderPaid = settings.AutoCreateInvoiceOnOrderPaid,
            AutoSendToGIB = settings.AutoSendToGIB,
            UseTestEnvironment = settings.UseTestEnvironment,
            IsActive = settings.IsActive
        };
    }
}

