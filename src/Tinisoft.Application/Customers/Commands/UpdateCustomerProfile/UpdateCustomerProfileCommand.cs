using MediatR;
using Tinisoft.Application.Customers.Models;

namespace Tinisoft.Application.Customers.Commands.UpdateCustomerProfile;

public class UpdateCustomerProfileCommand : IRequest<CustomerDto>
{
    public string? FirstName { get; set; }
    public string? LastName { get; set; }
    public string? Phone { get; set; }
    public string? Password { get; set; }
    public string? NewPassword { get; set; }
}




