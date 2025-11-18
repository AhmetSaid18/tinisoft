using MediatR;
using Tinisoft.Application.Customers.Models;

namespace Tinisoft.Application.Customers.Queries.GetCustomerAddresses;

public class GetCustomerAddressesQuery : IRequest<List<CustomerAddressDto>>
{
}


