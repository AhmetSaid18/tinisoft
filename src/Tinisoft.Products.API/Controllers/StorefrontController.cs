using MediatR;
using Microsoft.AspNetCore.Mvc;
using Tinisoft.Application.Products.Queries.GetStorefrontProducts;
using Tinisoft.Application.Products.Queries.GetStorefrontProduct;
using Tinisoft.Application.Products.Queries.GetStorefrontCategories;
using Tinisoft.Products.API.Attributes;

namespace Tinisoft.Products.API.Controllers;

/// <summary>
/// Storefront için public endpoint'ler (müşteriler için - tenant'ın seçtiği kura göre fiyat gösterimi)
/// </summary>
[ApiController]
[Route("api/storefront")]
public class StorefrontController : ControllerBase
{
    private readonly IMediator _mediator;
    private readonly ILogger<StorefrontController> _logger;

    public StorefrontController(IMediator mediator, ILogger<StorefrontController> logger)
    {
        _mediator = mediator;
        _logger = logger;
    }

    /// <summary>
    /// Storefront ürün listesi (public - tenant'ın seçtiği kura göre fiyat)
    /// </summary>
    [HttpGet("products")]
    [Public]
    public async Task<ActionResult<GetStorefrontProductsResponse>> GetProducts([FromQuery] GetStorefrontProductsQuery query)
    {
        var result = await _mediator.Send(query);
        return Ok(result);
    }

    /// <summary>
    /// Storefront ürün detayı (public - tenant'ın seçtiği kura göre fiyat)
    /// </summary>
    [HttpGet("products/{id}")]
    [Public]
    public async Task<ActionResult<GetStorefrontProductResponse>> GetProduct(Guid id, [FromQuery] string? preferredCurrency = null)
    {
        var query = new GetStorefrontProductQuery 
        { 
            ProductId = id,
            PreferredCurrency = preferredCurrency
        };
        var result = await _mediator.Send(query);
        return Ok(result);
    }

    /// <summary>
    /// Storefront kategori listesi (public)
    /// </summary>
    [HttpGet("categories")]
    [Public]
    public async Task<ActionResult<GetStorefrontCategoriesResponse>> GetCategories()
    {
        var query = new GetStorefrontCategoriesQuery();
        var result = await _mediator.Send(query);
        return Ok(result);
    }
}

