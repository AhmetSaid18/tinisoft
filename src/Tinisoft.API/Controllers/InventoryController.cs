using MediatR;
using Microsoft.AspNetCore.Mvc;
using Tinisoft.API.Controllers;
using Tinisoft.API.Attributes;
using Tinisoft.Application.Inventory.Commands.AdjustStock;
using Tinisoft.Application.Inventory.Commands.PickOrderItem;
using Tinisoft.Application.Inventory.Commands.TransferStock;
using Tinisoft.Application.Inventory.Commands.CreateWarehouseLocation;
using Tinisoft.Application.Inventory.Commands.CountInventory;
using Tinisoft.Application.Inventory.Queries.GetStockLevel;
using Tinisoft.Application.Inventory.Queries.GetPickingList;
using Tinisoft.Application.Inventory.Queries.GetStockMovements;
using Tinisoft.Application.Inventory.Queries.GetLowStockAlerts;
using Tinisoft.Application.Inventory.Queries.GetWarehouseStock;

namespace Tinisoft.API.Controllers;

[ApiController]
[Route("api/[controller]")]
public class InventoryController : BaseController
{
    private readonly IMediator _mediator;
    private readonly ILogger<InventoryController> _logger;

    public InventoryController(IMediator mediator, ILogger<InventoryController> logger)
    {
        _mediator = mediator;
        _logger = logger;
    }

    [HttpGet("products/{productId}")]
    [Public] // Public - müşteriler stok durumunu görebilir
    public async Task<ActionResult<GetStockLevelResponse>> GetStockLevel(
        Guid productId, 
        [FromQuery] Guid? variantId = null)
    {
        var query = new GetStockLevelQuery 
        { 
            ProductId = productId, 
            VariantId = variantId 
        };
        var result = await _mediator.Send(query);
        return Ok(result);
    }

    [HttpPost("adjust")]
    [RequireRole("TenantAdmin", "SystemAdmin")]
    public async Task<ActionResult<AdjustStockResponse>> AdjustStock([FromBody] AdjustStockCommand command)
    {
        var result = await _mediator.Send(command);
        return Ok(result);
    }

    [HttpGet("orders/{orderId}/picking-list")]
    [RequireRole("TenantAdmin", "SystemAdmin")]
    public async Task<ActionResult<GetPickingListResponse>> GetPickingList(Guid orderId)
    {
        var query = new GetPickingListQuery { OrderId = orderId };
        var result = await _mediator.Send(query);
        return Ok(result);
    }

    [HttpPost("pick")]
    [RequireRole("TenantAdmin", "SystemAdmin")]
    public async Task<ActionResult<PickOrderItemResponse>> PickOrderItem([FromBody] PickOrderItemCommand command)
    {
        var result = await _mediator.Send(command);
        return Ok(result);
    }

    [HttpPost("transfer")]
    [RequireRole("TenantAdmin", "SystemAdmin")]
    public async Task<ActionResult<TransferStockResponse>> TransferStock([FromBody] TransferStockCommand command)
    {
        var result = await _mediator.Send(command);
        return Ok(result);
    }

    [HttpPost("locations")]
    [RequireRole("TenantAdmin", "SystemAdmin")]
    public async Task<ActionResult<CreateWarehouseLocationResponse>> CreateWarehouseLocation([FromBody] CreateWarehouseLocationCommand command)
    {
        var result = await _mediator.Send(command);
        return CreatedAtAction(nameof(CreateWarehouseLocation), new { id = result.LocationId }, result);
    }

    /// <summary>
    /// Stok hareket geçmişi
    /// </summary>
    [HttpGet("movements")]
    [RequireRole("TenantAdmin", "SystemAdmin")]
    public async Task<ActionResult<GetStockMovementsResponse>> GetStockMovements([FromQuery] GetStockMovementsQuery query)
    {
        var result = await _mediator.Send(query);
        return Ok(result);
    }

    /// <summary>
    /// Düşük stok uyarıları (MinStockLevel'a düşen ürünler)
    /// </summary>
    [HttpGet("alerts/low-stock")]
    [RequireRole("TenantAdmin", "SystemAdmin")]
    public async Task<ActionResult<GetLowStockAlertsResponse>> GetLowStockAlerts([FromQuery] GetLowStockAlertsQuery query)
    {
        var result = await _mediator.Send(query);
        return Ok(result);
    }

    /// <summary>
    /// Stok sayımı (Inventory Count)
    /// </summary>
    [HttpPost("count")]
    [RequireRole("TenantAdmin", "SystemAdmin")]
    public async Task<ActionResult<CountInventoryResponse>> CountInventory([FromBody] CountInventoryCommand command)
    {
        var result = await _mediator.Send(command);
        return Ok(result);
    }

    /// <summary>
    /// Warehouse bazlı stok listesi
    /// </summary>
    [HttpGet("warehouse-stock")]
    [RequireRole("TenantAdmin", "SystemAdmin")]
    public async Task<ActionResult<GetWarehouseStockResponse>> GetWarehouseStock([FromQuery] GetWarehouseStockQuery query)
    {
        var result = await _mediator.Send(query);
        return Ok(result);
    }
}

