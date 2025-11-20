using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Domain.Entities;
using Tinisoft.Application.Common.Interfaces;
using Tinisoft.Shared.Contracts;
using Finbuckle.MultiTenant;

namespace Tinisoft.Application.Resellers.Commands.CreateReseller;

public class CreateResellerCommandHandler : IRequestHandler<CreateResellerCommand, CreateResellerResponse>
{
    private readonly IApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly ILogger<CreateResellerCommandHandler> _logger;

    public CreateResellerCommandHandler(
        IApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor,
        ILogger<CreateResellerCommandHandler> logger)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
        _logger = logger;
    }

    public async Task<CreateResellerResponse> Handle(CreateResellerCommand request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        // Email kontrolü (aynı tenant'ta unique olmalı)
        var existingReseller = await _dbContext.Resellers
            .FirstOrDefaultAsync(r => r.TenantId == tenantId && r.Email == request.Email, cancellationToken);

        if (existingReseller != null)
        {
            throw new InvalidOperationException($"Bu email adresi zaten kullanılıyor: {request.Email}");
        }

        var reseller = new Reseller
        {
            TenantId = tenantId,
            CompanyName = request.CompanyName,
            TaxNumber = request.TaxNumber,
            TaxOffice = request.TaxOffice,
            Email = request.Email,
            Phone = request.Phone,
            Mobile = request.Mobile,
            Address = request.Address,
            City = request.City,
            State = request.State,
            PostalCode = request.PostalCode,
            Country = request.Country,
            ContactPersonName = request.ContactPersonName,
            ContactPersonTitle = request.ContactPersonTitle,
            IsActive = true,
            CreditLimit = request.CreditLimit,
            PaymentTermDays = request.PaymentTermDays,
            PaymentMethod = request.PaymentMethod,
            DefaultDiscountPercent = request.DefaultDiscountPercent,
            UseCustomPricing = request.UseCustomPricing,
            Notes = request.Notes
        };

        _dbContext.Resellers.Add(reseller);
        await _dbContext.SaveChangesAsync(cancellationToken);

        _logger.LogInformation("Reseller created: {ResellerId}, Company: {CompanyName}", reseller.Id, reseller.CompanyName);

        return new CreateResellerResponse
        {
            ResellerId = reseller.Id,
            CompanyName = reseller.CompanyName,
            Email = reseller.Email
        };
    }
}



