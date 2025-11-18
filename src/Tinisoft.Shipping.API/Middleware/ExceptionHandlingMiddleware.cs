using System.Net;
using System.Text.Json;
using Tinisoft.Application.Common.Exceptions;

namespace Tinisoft.Shipping.API.Middleware;

public class ExceptionHandlingMiddleware
{
    private readonly RequestDelegate _next;
    private readonly ILogger<ExceptionHandlingMiddleware> _logger;

    public ExceptionHandlingMiddleware(RequestDelegate next, ILogger<ExceptionHandlingMiddleware> logger)
    {
        _next = next;
        _logger = logger;
    }

    public async Task InvokeAsync(HttpContext context)
    {
        try
        {
            await _next(context);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "An error occurred: {Message}", ex.Message);
            await HandleExceptionAsync(context, ex);
        }
    }

    private static Task HandleExceptionAsync(HttpContext context, Exception exception)
    {
        var code = HttpStatusCode.InternalServerError;
        var result = string.Empty;

        switch (exception)
        {
            case NotFoundException notFoundException:
                code = HttpStatusCode.NotFound;
                result = JsonSerializer.Serialize(new { error = notFoundException.Message });
                break;
            case BadRequestException badRequestException:
                code = HttpStatusCode.BadRequest;
                result = JsonSerializer.Serialize(new { error = badRequestException.Message });
                break;
            case UnauthorizedException unauthorizedException:
                code = HttpStatusCode.Unauthorized;
                result = JsonSerializer.Serialize(new { error = unauthorizedException.Message });
                break;
            case ValidationException validationException:
                code = HttpStatusCode.BadRequest;
                result = JsonSerializer.Serialize(new { errors = validationException.Errors });
                break;
            default:
                result = JsonSerializer.Serialize(new { error = "An error occurred while processing your request." });
                break;
        }

        context.Response.ContentType = "application/json";
        context.Response.StatusCode = (int)code;

        return context.Response.WriteAsync(result);
    }
}

