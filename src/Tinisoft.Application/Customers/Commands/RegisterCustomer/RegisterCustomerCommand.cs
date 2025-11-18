using MediatR;

namespace Tinisoft.Application.Customers.Commands.RegisterCustomer;

public class RegisterCustomerCommand : IRequest<CustomerAuthResponse>
{
    public string Email { get; set; } = string.Empty;
    public string Password { get; set; } = string.Empty;
    public string? FirstName { get; set; }
    public string? LastName { get; set; }
    public string? Phone { get; set; }
}

public class CustomerAuthResponse
{
    public Guid CustomerId { get; set; }
    public string Email { get; set; } = string.Empty;
    public string? FirstName { get; set; }
    public string? LastName { get; set; }
    public string? Phone { get; set; }
    public string Token { get; set; } = string.Empty;
}


