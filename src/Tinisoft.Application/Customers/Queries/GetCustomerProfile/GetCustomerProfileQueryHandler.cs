using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Application.Common.Interfaces;
using Tinisoft.Application.Customers.Models;
using Tinisoft.Infrastructure.Persistence;

namespace Tinisoft.Application.Customers.Queries.GetCustomerProfile;

public class GetCustomerProfileQueryHandler : IRequestHandler<GetCustomerProfileQuery, CustomerDto>
{
    private readonly ApplicationDbContext _dbContext;
    private readonly ICurrentCustomerService _currentCustomerService;

    public GetCustomerProfileQueryHandler(
        ApplicationDbContext dbContext,
        ICurrentCustomerService currentCustomerService)
    {
        _dbContext = dbContext;
        _currentCustomerService = currentCustomerService;
    }

    public async Task<CustomerDto> Handle(GetCustomerProfileQuery request, CancellationToken cancellationToken)
    {
        var customerId = _currentCustomerService.GetCurrentCustomerId();
        if (!customerId.HasValue)
        {
            throw new InvalidOperationException("Müşteri bilgisi bulunamadı.");
        }

        var customer = await _dbContext.Customers
            .AsNoTracking()
            .FirstOrDefaultAsync(c => c.Id == customerId.Value, cancellationToken);

        if (customer == null)
        {
            throw new KeyNotFoundException("Müşteri bulunamadı.");
        }

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


