using MediatR;

namespace Tinisoft.Application.Products.Commands.DeleteProduct;

public class DeleteProductCommand : IRequest<Unit>
{
    public Guid ProductId { get; set; }
}



