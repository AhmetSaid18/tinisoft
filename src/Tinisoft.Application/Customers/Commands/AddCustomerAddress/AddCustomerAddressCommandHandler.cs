using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Application.Common.Interfaces;
using Tinisoft.Application.Customers.Models;
using Tinisoft.Domain.Entities;
using Tinisoft.Infrastructure.Persistence;

namespace Tinisoft.Application.Customers.Commands.AddCustomerAddress;

public class AddCustomerAddressCommandHandler : IRequestHandler<AddCustomerAddressCommand, CustomerAddressDto>
{
    private readonly ApplicationDbContext _dbContext;
    private readonly ICurrentCustomerService _currentCustomerService;

    public AddCustomerAddressCommandHandler(
        ApplicationDbContext dbContext,
        ICurrentCustomerService currentCustomerService)
    {
        _dbContext = dbContext;
        _currentCustomerService = currentCustomerService;
    }

    public async Task<CustomerAddressDto> Handle(AddCustomerAddressCommand request, CancellationToken cancellationToken)
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

        var address = new CustomerAddress
        {
            TenantId = customer.TenantId,
            CustomerId = customer.Id,
            AddressLine1 = request.AddressLine1,
            AddressLine2 = request.AddressLine2,
            City = request.City,
            State = request.State,
            PostalCode = request.PostalCode,
            Country = request.Country,
            Phone = request.Phone,
            AddressTitle = request.AddressTitle,
            IsDefaultShipping = request.IsDefaultShipping,
            IsDefaultBilling = request.IsDefaultBilling
        };

        _dbContext.CustomerAddresses.Add(address);

        await _dbContext.SaveChangesAsync(cancellationToken);

        // Default address güncellemeleri
        if (request.IsDefaultShipping)
        {
            await _dbContext.CustomerAddresses
                .Where(ca => ca.CustomerId == customer.Id && ca.Id != address.Id && ca.IsDefaultShipping)
                .ExecuteUpdateAsync(updates => updates.SetProperty(ca => ca.IsDefaultShipping, false), cancellationToken);

            customer.DefaultShippingAddressId = address.Id;
        }

        if (request.IsDefaultBilling)
        {
            await _dbContext.CustomerAddresses
                .Where(ca => ca.CustomerId == customer.Id && ca.Id != address.Id && ca.IsDefaultBilling)
                .ExecuteUpdateAsync(updates => updates.SetProperty(ca => ca.IsDefaultBilling, false), cancellationToken);

            customer.DefaultBillingAddressId = address.Id;
        }

        await _dbContext.SaveChangesAsync(cancellationToken);

        return new CustomerAddressDto
        {
            AddressId = address.Id,
            AddressLine1 = address.AddressLine1,
            AddressLine2 = address.AddressLine2,
            City = address.City,
            State = address.State,
            PostalCode = address.PostalCode,
            Country = address.Country,
            Phone = address.Phone,
            AddressTitle = address.AddressTitle,
            IsDefaultShipping = address.IsDefaultShipping,
            IsDefaultBilling = address.IsDefaultBilling
        };
    }
}


