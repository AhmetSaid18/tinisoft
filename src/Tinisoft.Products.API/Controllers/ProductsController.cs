using MediatR;
using Microsoft.AspNetCore.Mvc;
using Tinisoft.Application.Products.Commands.CreateProduct;
using Tinisoft.Application.Products.Commands.UpdateProduct;
using Tinisoft.Application.Products.Commands.DeleteProduct;
using Tinisoft.Application.Products.Queries.GetProduct;
using Tinisoft.Application.Products.Queries.GetProducts;

namespace Tinisoft.Products.API.Controllers;

[ApiController]
[Route("api/products")]
public class ProductsController : ControllerBase
{
    private readonly IMediator _mediator;
    private readonly ILogger<ProductsController> _logger;

    public ProductsController(IMediator mediator, ILogger<ProductsController> logger)
    {
        _mediator = mediator;
        _logger = logger;
    }

    [HttpGet]
    public async Task<ActionResult<GetProductsResponse>> GetProducts([FromQuery] GetProductsQuery query)
    {
        var result = await _mediator.Send(query);
        return Ok(result);
    }

    [HttpGet("{id}")]
    public async Task<ActionResult<GetProductResponse>> GetProduct(Guid id)
    {
        var query = new GetProductQuery { ProductId = id };
        var result = await _mediator.Send(query);
        return Ok(result);
    }

    [HttpPost]
    public async Task<ActionResult<CreateProductResponse>> CreateProduct([FromBody] CreateProductCommand command)
    {
        var result = await _mediator.Send(command);
        return CreatedAtAction(nameof(GetProduct), new { id = result.ProductId }, result);
    }

    [HttpPut("{id}")]
    public async Task<ActionResult<UpdateProductResponse>> UpdateProduct(Guid id, [FromBody] UpdateProductCommand command)
    {
        command.ProductId = id;
        var result = await _mediator.Send(command);
        return Ok(result);
    }

    [HttpDelete("{id}")]
    public async Task<IActionResult> DeleteProduct(Guid id)
    {
        var command = new DeleteProductCommand { ProductId = id };
        await _mediator.Send(command);
        return NoContent();
    }
}

