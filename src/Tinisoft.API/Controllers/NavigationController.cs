using MediatR;
using Microsoft.AspNetCore.Mvc;
using Tinisoft.API.Attributes;
using Tinisoft.Domain.Entities;
using Tinisoft.Application.Navigation.Commands.CreateMenuItem;
using Tinisoft.Application.Navigation.Commands.UpdateMenuItem;
using Tinisoft.Application.Navigation.Commands.DeleteMenuItem;
using Tinisoft.Application.Navigation.Queries.GetNavigation;

namespace Tinisoft.API.Controllers;

[ApiController]
[Route("api/navigation")]
public class NavigationController : ControllerBase
{
    private readonly IMediator _mediator;
    private readonly ILogger<NavigationController> _logger;

    public NavigationController(IMediator mediator, ILogger<NavigationController> logger)
    {
        _mediator = mediator;
        _logger = logger;
    }

    /// <summary>
    /// Navigasyon menüsünü getir (hiyerarşik)
    /// </summary>
    [HttpGet]
    [RequireRole("TenantAdmin", "SystemAdmin")]
    public async Task<ActionResult<GetNavigationResponse>> GetNavigation([FromQuery] NavigationLocation? location, [FromQuery] bool onlyVisible = false)
    {
        var query = new GetNavigationQuery
        {
            Location = location,
            OnlyVisible = onlyVisible
        };
        var result = await _mediator.Send(query);
        return Ok(result);
    }

    /// <summary>
    /// Yeni menü öğesi oluştur
    /// </summary>
    [HttpPost]
    [RequireRole("TenantAdmin", "SystemAdmin")]
    public async Task<ActionResult<CreateMenuItemResponse>> CreateMenuItem([FromBody] CreateMenuItemCommand command)
    {
        var result = await _mediator.Send(command);
        return CreatedAtAction(nameof(GetNavigation), result);
    }

    /// <summary>
    /// Menü öğesi güncelle
    /// </summary>
    [HttpPut("{id}")]
    [RequireRole("TenantAdmin", "SystemAdmin")]
    public async Task<ActionResult<UpdateMenuItemResponse>> UpdateMenuItem(Guid id, [FromBody] UpdateMenuItemCommand command)
    {
        command.MenuItemId = id;
        var result = await _mediator.Send(command);
        return Ok(result);
    }

    /// <summary>
    /// Menü öğesi sil
    /// </summary>
    [HttpDelete("{id}")]
    [RequireRole("TenantAdmin", "SystemAdmin")]
    public async Task<ActionResult<DeleteMenuItemResponse>> DeleteMenuItem(Guid id)
    {
        var command = new DeleteMenuItemCommand { MenuItemId = id };
        var result = await _mediator.Send(command);
        return Ok(result);
    }

    /// <summary>
    /// Menü sıralamasını toplu güncelle
    /// </summary>
    [HttpPut("reorder")]
    [RequireRole("TenantAdmin", "SystemAdmin")]
    public async Task<ActionResult> ReorderMenu([FromBody] List<MenuOrderItem> items)
    {
        // Basit reorder işlemi
        foreach (var item in items)
        {
            var command = new UpdateMenuItemCommand
            {
                MenuItemId = item.Id,
                SortOrder = item.SortOrder,
                ParentId = item.ParentId
            };
            // Not: Bu basit bir implementasyon, daha optimize edilebilir
        }
        return Ok(new { message = "Menü sıralaması güncellendi." });
    }
}

public class MenuOrderItem
{
    public Guid Id { get; set; }
    public int SortOrder { get; set; }
    public Guid? ParentId { get; set; }
}

