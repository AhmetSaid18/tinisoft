using MediatR;
using Microsoft.AspNetCore.Mvc;
using Tinisoft.API.Attributes;
using Tinisoft.Application.Templates.Queries.GetBootstrapData;
using Tinisoft.Application.Storefront.Queries.GetStorefrontNavigation;
using Tinisoft.Application.Storefront.Queries.GetStorefrontPage;

namespace Tinisoft.API.Controllers;

/// <summary>
/// Storefront API - Frontend için public endpoint'ler
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
    /// Bootstrap data - Frontend ilk yüklendiğinde çağırır
    /// Tema, ayarlar, renkler, logo vs. döner
    /// </summary>
    [HttpGet("bootstrap")]
    [Public]
    public async Task<ActionResult<GetBootstrapDataResponse>> GetBootstrapData()
    {
        var result = await _mediator.Send(new GetBootstrapDataQuery());
        return Ok(result);
    }

    /// <summary>
    /// Navigasyon menüsü - Header, Footer, Mobile menüleri
    /// </summary>
    [HttpGet("navigation")]
    [Public]
    public async Task<ActionResult<GetStorefrontNavigationResponse>> GetNavigation()
    {
        var result = await _mediator.Send(new GetStorefrontNavigationQuery());
        return Ok(result);
    }

    /// <summary>
    /// Sayfa içeriği - Hakkımızda, İletişim, KVKK vs.
    /// </summary>
    [HttpGet("pages/{slug}")]
    [Public]
    public async Task<ActionResult<GetStorefrontPageResponse>> GetPage(string slug)
    {
        var result = await _mediator.Send(new GetStorefrontPageQuery { Slug = slug });
        
        if (result == null)
        {
            return NotFound(new { message = "Sayfa bulunamadı." });
        }
        
        return Ok(result);
    }
}

