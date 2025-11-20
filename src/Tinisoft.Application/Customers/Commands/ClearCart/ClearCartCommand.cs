using MediatR;

namespace Tinisoft.Application.Customers.Commands.ClearCart;

public class ClearCartCommand : IRequest<ClearCartResponse>
{
}

public class ClearCartResponse
{
    public bool Success { get; set; }
}



