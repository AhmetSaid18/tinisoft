using Microsoft.AspNetCore.Mvc;
using Tinisoft.Application.ProductFeeds.Services;
using Tinisoft.API.Attributes;

namespace Tinisoft.API.Controllers;

[ApiController]
[Route("api/public/feeds")]
[Public] // Public endpoint - feed'ler herkese açık
public class PublicFeedsController : ControllerBase
{
    private readonly IProductFeedService _feedService;
    private readonly ILogger<PublicFeedsController> _logger;

    public PublicFeedsController(
        IProductFeedService feedService,
        ILogger<PublicFeedsController> logger)
    {
        _feedService = feedService;
        _logger = logger;
    }

    /// <summary>
    /// Google Shopping XML feed
    /// </summary>
    [HttpGet("google-shopping.xml")]
    [Produces("application/xml")]
    public async Task<IActionResult> GetGoogleShoppingFeed()
    {
        try
        {
            var xml = await _feedService.GenerateGoogleShoppingFeedAsync();
            return Content(xml, "application/xml", System.Text.Encoding.UTF8);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error generating Google Shopping feed");
            return StatusCode(500, "Feed oluşturulurken hata oluştu");
        }
    }

    /// <summary>
    /// Cimri XML feed
    /// </summary>
    [HttpGet("cimri.xml")]
    [Produces("application/xml")]
    public async Task<IActionResult> GetCimriFeed()
    {
        try
        {
            var xml = await _feedService.GenerateCimriFeedAsync();
            return Content(xml, "application/xml", System.Text.Encoding.UTF8);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error generating Cimri feed");
            return StatusCode(500, "Feed oluşturulurken hata oluştu");
        }
    }

    /// <summary>
    /// Custom XML feed (format parametresi ile)
    /// </summary>
    [HttpGet("products.xml")]
    [Produces("application/xml")]
    public async Task<IActionResult> GetCustomFeed([FromQuery] string? format = "google")
    {
        try
        {
            var xml = await _feedService.GenerateCustomFeedAsync(format ?? "google");
            return Content(xml, "application/xml", System.Text.Encoding.UTF8);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error generating custom feed");
            return StatusCode(500, "Feed oluşturulurken hata oluştu");
        }
    }
}

