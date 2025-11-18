using MediatR;
using Tinisoft.Application.Customers.Models;

namespace Tinisoft.Application.Customers.Commands.AddCustomerAddress;

public class AddCustomerAddressCommand : IRequest<CustomerAddressDto>
{
    public string AddressLine1 { get; set; } = string.Empty;
    public string? AddressLine2 { get; set; }
    public string City { get; set; } = string.Empty;
    public string? State { get; set; }
    public string PostalCode { get; set; } = string.Empty;
    public string Country { get; set; } = "TR";
    public string? Phone { get; set; }
    public string? AddressTitle { get; set; }
    public bool IsDefaultShipping { get; set; }
    public bool IsDefaultBilling { get; set; }
}


