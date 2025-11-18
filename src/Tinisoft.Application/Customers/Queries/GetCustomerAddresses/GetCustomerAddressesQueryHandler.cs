using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Application.Common.Interfaces;
using Tinisoft.Application.Customers.Models;
using Tinisoft.Infrastructure.Persistence;

namespace Tinisoft.Application.Customers.Queries.GetCustomerAddresses;

public class GetCustomerAddressesQueryHandler : IRequestHandler<GetCustomerAddressesQuery, List<CustomerAddressDto>>
{
    private readonly ApplicationDbContext _dbContext;
    private readonly ICurrentCustomerService _currentCustomerService;

    public GetCustomerAddressesQueryHandler(
        ApplicationDbContext dbContext,
        ICurrentCustomerService currentCustomerService)
    {
        _dbContext = dbContext;
        _currentCustomerService = currentCustomerService;
    }

    public async Task<List<CustomerAddressDto>> Handle(GetCustomerAddressesQuery request, CancellationToken cancellationToken)
    {
        var customerId = _currentCustomerService.GetCurrentCustomerId();
        if (!customerId.HasValue)
        {
            throw new InvalidOperationException("Müşteri bilgisi bulunamadı.");
        }

        var addresses = await _dbContext.CustomerAddresses
            .Where(ca => ca.CustomerId == customerId.Value)
            .OrderByDescending(ca => ca.CreatedAt)
            .Select(ca => new CustomerAddressDto
            {
                AddressId = ca.Id,
                AddressLine1 = ca.AddressLine1,
                AddressLine2 = ca.AddressLine2,
                City = ca.City,
                State = ca.State,
                PostalCode = ca.PostalCode,
                Country = ca.Country,
                Phone = ca.Phone,
                AddressTitle = ca.AddressTitle,
                IsDefaultShipping = ca.IsDefaultShipping,
                IsDefaultBilling = ca.IsDefaultBilling
            })
            .ToListAsync(cancellationToken);

        return addresses;
    }
}


