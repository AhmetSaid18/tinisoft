using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Application.Customers.Models;
using Tinisoft.Domain.Entities;
using Tinisoft.Application.Common.Interfaces;
using Tinisoft.Shared.Contracts;
using Tinisoft.Application.Common.Interfaces;
using Finbuckle.MultiTenant;

namespace Tinisoft.Application.Customers.Commands.RegisterCustomer;

public class RegisterCustomerCommandHandler : IRequestHandler<RegisterCustomerCommand, CustomerAuthResponse>
{
    private readonly IApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly IPasswordHasher _passwordHasher;
    private readonly IJwtTokenService _jwtTokenService;
    private readonly ILogger<RegisterCustomerCommandHandler> _logger;

    public RegisterCustomerCommandHandler(
        IApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor,
        IPasswordHasher passwordHasher,
        IJwtTokenService jwtTokenService,
        ILogger<RegisterCustomerCommandHandler> logger)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
        _passwordHasher = passwordHasher;
        _jwtTokenService = jwtTokenService;
        _logger = logger;
    }

    public async Task<CustomerAuthResponse> Handle(RegisterCustomerCommand request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        var normalizedEmail = request.Email.Trim().ToLowerInvariant();

        // Email kontrolü
        var existingCustomer = await _dbContext.Customers
            .FirstOrDefaultAsync(c => c.TenantId == tenantId && c.Email == normalizedEmail, cancellationToken);

        if (existingCustomer != null)
        {
            throw new InvalidOperationException("Bu email adresi ile kayıtlı bir müşteri zaten mevcut.");
        }

        var passwordHash = _passwordHasher.HashPassword(request.Password);

        var customer = new Customer
        {
            TenantId = tenantId,
            Email = normalizedEmail,
            PasswordHash = passwordHash,
            FirstName = request.FirstName,
            LastName = request.LastName,
            Phone = request.Phone,
            EmailVerified = false,
            IsActive = true
        };

        _dbContext.Customers.Add(customer);
        await _dbContext.SaveChangesAsync(cancellationToken);

        var token = _jwtTokenService.GenerateToken(customer.Id, customer.Email, "Customer", tenantId);

        _logger.LogInformation("Customer registered: {CustomerId}, Tenant: {TenantId}", customer.Id, tenantId);

        return new CustomerAuthResponse
        {
            CustomerId = customer.Id,
            Email = customer.Email,
            FirstName = customer.FirstName,
            LastName = customer.LastName,
            Phone = customer.Phone,
            Token = token
        };
    }
}




