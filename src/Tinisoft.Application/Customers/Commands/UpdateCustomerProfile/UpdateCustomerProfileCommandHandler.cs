using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Application.Common.Interfaces;
using Tinisoft.Application.Customers.Models;
using Tinisoft.Infrastructure.Persistence;

namespace Tinisoft.Application.Customers.Commands.UpdateCustomerProfile;

public class UpdateCustomerProfileCommandHandler : IRequestHandler<UpdateCustomerProfileCommand, CustomerDto>
{
    private readonly ApplicationDbContext _dbContext;
    private readonly ICurrentCustomerService _currentCustomerService;
    private readonly IPasswordHasher _passwordHasher;

    public UpdateCustomerProfileCommandHandler(
        ApplicationDbContext dbContext,
        ICurrentCustomerService currentCustomerService,
        IPasswordHasher passwordHasher)
    {
        _dbContext = dbContext;
        _currentCustomerService = currentCustomerService;
        _passwordHasher = passwordHasher;
    }

    public async Task<CustomerDto> Handle(UpdateCustomerProfileCommand request, CancellationToken cancellationToken)
    {
        var customerId = _currentCustomerService.GetCurrentCustomerId();
        if (!customerId.HasValue)
        {
            throw new InvalidOperationException("Müşteri bilgisi bulunamadı.");
        }

        var customer = await _dbContext.Customers
            .FirstOrDefaultAsync(c => c.Id == customerId.Value, cancellationToken);

        if (customer == null)
        {
            throw new KeyNotFoundException("Müşteri bulunamadı.");
        }

        if (!string.IsNullOrEmpty(request.NewPassword))
        {
            if (string.IsNullOrEmpty(request.Password))
            {
                throw new InvalidOperationException("Mevcut şifre gerekli.");
            }

            if (!_passwordHasher.VerifyPassword(request.Password, customer.PasswordHash))
            {
                throw new InvalidOperationException("Mevcut şifre hatalı.");
            }

            customer.PasswordHash = _passwordHasher.HashPassword(request.NewPassword);
        }

        if (request.FirstName != null) customer.FirstName = request.FirstName;
        if (request.LastName != null) customer.LastName = request.LastName;
        if (request.Phone != null) customer.Phone = request.Phone;

        customer.UpdatedAt = DateTime.UtcNow;

        await _dbContext.SaveChangesAsync(cancellationToken);

        return new CustomerDto
        {
            Id = customer.Id,
            Email = customer.Email,
            FirstName = customer.FirstName,
            LastName = customer.LastName,
            Phone = customer.Phone,
            EmailVerified = customer.EmailVerified,
            CreatedAt = customer.CreatedAt
        };
    }
}


