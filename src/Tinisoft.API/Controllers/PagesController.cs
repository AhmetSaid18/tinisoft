using MediatR;
using Microsoft.AspNetCore.Mvc;
using Tinisoft.API.Attributes;
using Tinisoft.Application.Pages.Commands.CreatePage;
using Tinisoft.Application.Pages.Commands.UpdatePage;
using Tinisoft.Application.Pages.Commands.DeletePage;
using Tinisoft.Application.Pages.Queries.GetPages;
using Tinisoft.Application.Pages.Queries.GetPage;

namespace Tinisoft.API.Controllers;

[ApiController]
[Route("api/pages")]
public class PagesController : ControllerBase
{
    private readonly IMediator _mediator;
    private readonly ILogger<PagesController> _logger;

    public PagesController(IMediator mediator, ILogger<PagesController> logger)
    {
        _mediator = mediator;
        _logger = logger;
    }

    /// <summary>
    /// Tüm sayfaları listele
    /// </summary>
    [HttpGet]
    [RequireRole("TenantAdmin", "SystemAdmin")]
    public async Task<ActionResult<GetPagesResponse>> GetPages([FromQuery] GetPagesQuery query)
    {
        var result = await _mediator.Send(query);
        return Ok(result);
    }

    /// <summary>
    /// Sayfa detayı getir (ID veya Slug ile)
    /// </summary>
    [HttpGet("{idOrSlug}")]
    [RequireRole("TenantAdmin", "SystemAdmin")]
    public async Task<ActionResult<GetPageResponse>> GetPage(string idOrSlug)
    {
        var query = new GetPageQuery();
        
        if (Guid.TryParse(idOrSlug, out var id))
        {
            query.PageId = id;
        }
        else
        {
            query.Slug = idOrSlug;
        }

        var result = await _mediator.Send(query);
        return Ok(result);
    }

    /// <summary>
    /// Yeni sayfa oluştur
    /// </summary>
    [HttpPost]
    [RequireRole("TenantAdmin", "SystemAdmin")]
    public async Task<ActionResult<CreatePageResponse>> CreatePage([FromBody] CreatePageCommand command)
    {
        var result = await _mediator.Send(command);
        return CreatedAtAction(nameof(GetPage), new { idOrSlug = result.PageId }, result);
    }

    /// <summary>
    /// Sayfa güncelle
    /// </summary>
    [HttpPut("{id}")]
    [RequireRole("TenantAdmin", "SystemAdmin")]
    public async Task<ActionResult<UpdatePageResponse>> UpdatePage(Guid id, [FromBody] UpdatePageCommand command)
    {
        command.PageId = id;
        var result = await _mediator.Send(command);
        return Ok(result);
    }

    /// <summary>
    /// Sayfa sil
    /// </summary>
    [HttpDelete("{id}")]
    [RequireRole("TenantAdmin", "SystemAdmin")]
    public async Task<ActionResult<DeletePageResponse>> DeletePage(Guid id)
    {
        var command = new DeletePageCommand { PageId = id };
        var result = await _mediator.Send(command);
        return Ok(result);
    }
}

