using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Domain.Entities;
using Tinisoft.Infrastructure.Persistence;
using Tinisoft.Infrastructure.Services;
using Tinisoft.Application.Common.Interfaces;
using Finbuckle.MultiTenant;

namespace Tinisoft.Application.Customers.Commands.LoginCustomer;

public class LoginCustomerCommandHandler : IRequestHandler<LoginCustomerCommand, CustomerLoginResponse>
{
    private readonly ApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly IPasswordHasher _passwordHasher;
    private readonly IJwtTokenService _jwtTokenService;
    private readonly ILogger<LoginCustomerCommandHandler> _logger;

    public LoginCustomerCommandHandler(
        ApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor,
        IPasswordHasher passwordHasher,
        IJwtTokenService jwtTokenService,
        ILogger<LoginCustomerCommandHandler> logger)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
        _passwordHasher = passwordHasher;
        _jwtTokenService = jwtTokenService;
        _logger = logger;
    }

    public async Task<CustomerLoginResponse> Handle(LoginCustomerCommand request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);
        var email = request.Email.Trim().ToLowerInvariant();

        var customer = await _dbContext.Customers
            .FirstOrDefaultAsync(c => c.TenantId == tenantId && c.Email == email, cancellationToken);

        if (customer == null || !_passwordHasher.VerifyPassword(request.Password, customer.PasswordHash))
        {
            throw new InvalidOperationException("Email veya şifre hatalı.");
        }

        if (!customer.IsActive)
        {
            throw new InvalidOperationException("Hesabınız pasif. Lütfen destek ile iletişime geçiniz.");
        }

        customer.LastLoginAt = DateTime.UtcNow;
        await _dbContext.SaveChangesAsync(cancellationToken);

        var token = _jwtTokenService.GenerateToken(customer.Id, customer.Email, "Customer", tenantId);

        _logger.LogInformation("Customer login: {CustomerId}, Tenant: {TenantId}", customer.Id, tenantId);

        return new CustomerLoginResponse
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


