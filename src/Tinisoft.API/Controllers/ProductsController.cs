using MediatR;
using Microsoft.AspNetCore.Mvc;
using Tinisoft.API.Controllers;
using Tinisoft.API.Attributes;
using Tinisoft.Application.Products.Commands.CreateProduct;
using Tinisoft.Application.Products.Commands.UpdateProduct;
using Tinisoft.Application.Products.Commands.DeleteProduct;
using Tinisoft.Application.Products.Queries.GetProduct;
using Tinisoft.Application.Products.Queries.GetProducts;
using Tinisoft.Application.Products.Queries.GetProductsCursor;

namespace Tinisoft.API.Controllers;

[ApiController]
[Route("api/[controller]")]
public class ProductsController : BaseController
{
    private readonly IMediator _mediator;
    private readonly ILogger<ProductsController> _logger;

    public ProductsController(IMediator mediator, ILogger<ProductsController> logger)
    {
        _mediator = mediator;
        _logger = logger;
    }

    [HttpGet]
    [Public] // Public - müşteriler ürünleri görebilir
    public async Task<ActionResult<GetProductsResponse>> GetProducts([FromQuery] GetProductsQuery query)
    {
        var result = await _mediator.Send(query);
        return Ok(result);
    }

    [HttpGet("cursor")]
    [Public] // Public - Cursor-based pagination (Shopify tarzı, milyarlarca ürün için optimize)
    public async Task<ActionResult<GetProductsCursorResponse>> GetProductsCursor([FromQuery] GetProductsCursorQuery query)
    {
        var result = await _mediator.Send(query);
        return Ok(result);
    }

    [HttpGet("{id}")]
    [Public] // Public - müşteriler ürün detaylarını görebilir
    public async Task<ActionResult<GetProductResponse>> GetProduct(Guid id)
    {
        var query = new GetProductQuery { ProductId = id };
        var result = await _mediator.Send(query);
        return Ok(result);
    }

    [HttpPost]
    [RequireRole("TenantAdmin", "SystemAdmin")] // Sadece TenantAdmin ve SystemAdmin ürün ekleyebilir
    public async Task<ActionResult<CreateProductResponse>> CreateProduct([FromBody] CreateProductCommand command)
    {
        var result = await _mediator.Send(command);
        return CreatedAtAction(nameof(GetProduct), new { id = result.ProductId }, result);
    }

    [HttpPut("{id}")]
    [RequireRole("TenantAdmin", "SystemAdmin")] // Sadece TenantAdmin ve SystemAdmin ürün güncelleyebilir
    public async Task<ActionResult<UpdateProductResponse>> UpdateProduct(Guid id, [FromBody] UpdateProductCommand command)
    {
        command.ProductId = id;
        var result = await _mediator.Send(command);
        return Ok(result);
    }

    [HttpDelete("{id}")]
    [RequireRole("TenantAdmin", "SystemAdmin")] // Sadece TenantAdmin ve SystemAdmin ürün silebilir
    public async Task<IActionResult> DeleteProduct(Guid id)
    {
        var command = new DeleteProductCommand { ProductId = id };
        await _mediator.Send(command);
        return NoContent();
    }
}

