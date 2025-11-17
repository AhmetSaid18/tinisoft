using System.Net;
using System.Text.Json;
using FluentValidation;
using Tinisoft.Application.Common.Exceptions;

namespace Tinisoft.Orders.API.Middleware;

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
            _logger.LogError(ex, "Bir hata oluştu: {Message}", ex.Message);
            await HandleExceptionAsync(context, ex);
        }
    }

    private static Task HandleExceptionAsync(HttpContext context, Exception exception)
    {
        var code = HttpStatusCode.InternalServerError;
        object? response = null;

        switch (exception)
        {
            case ApiKeyMissingException apiKeyEx:
                code = HttpStatusCode.BadRequest;
                response = new
                {
                    error = apiKeyEx.Message,
                    code = "API_KEY_MISSING",
                    marketplace = apiKeyEx.Marketplace
                };
                break;

            case MarketplaceIntegrationNotFoundException integrationEx:
                code = HttpStatusCode.NotFound;
                response = new
                {
                    error = integrationEx.Message,
                    code = "MARKETPLACE_INTEGRATION_NOT_FOUND",
                    marketplace = integrationEx.Marketplace
                };
                break;

            case NotFoundException notFoundEx:
                code = HttpStatusCode.NotFound;
                response = new
                {
                    error = notFoundEx.Message,
                    code = "NOT_FOUND",
                    resource = notFoundEx.ResourceName,
                    key = notFoundEx.Key
                };
                break;

            case BadRequestException badRequestEx:
                code = HttpStatusCode.BadRequest;
                response = new
                {
                    error = badRequestEx.Message,
                    code = "BAD_REQUEST"
                };
                break;

            case UnauthorizedException unauthorizedEx:
                code = HttpStatusCode.Unauthorized;
                response = new
                {
                    error = unauthorizedEx.Message,
                    code = "UNAUTHORIZED"
                };
                break;

            case ValidationException validationEx:
                code = HttpStatusCode.BadRequest;
                response = new
                {
                    error = validationEx.Message,
                    code = "VALIDATION_ERROR",
                    errors = validationEx.Errors
                };
                break;

            case FluentValidation.ValidationException fluentValidationEx:
                code = HttpStatusCode.BadRequest;
                var errors = fluentValidationEx.Errors
                    .GroupBy(e => e.PropertyName)
                    .ToDictionary(
                        g => g.Key,
                        g => g.Select(e => e.ErrorMessage).ToArray()
                    );
                response = new
                {
                    error = "Doğrulama hatası oluştu.",
                    code = "VALIDATION_ERROR",
                    errors = errors
                };
                break;

            case ArgumentException argEx:
                code = HttpStatusCode.BadRequest;
                response = new
                {
                    error = argEx.Message,
                    code = "INVALID_ARGUMENT"
                };
                break;

            case InvalidOperationException invalidOpEx:
                code = HttpStatusCode.BadRequest;
                response = new
                {
                    error = invalidOpEx.Message,
                    code = "INVALID_OPERATION"
                };
                break;

            default:
                response = new
                {
                    error = "Bir hata oluştu. Lütfen daha sonra tekrar deneyin.",
                    code = "INTERNAL_SERVER_ERROR"
                };
                break;
        }

        var result = JsonSerializer.Serialize(response, new JsonSerializerOptions
        {
            PropertyNamingPolicy = JsonNamingPolicy.CamelCase
        });

        context.Response.ContentType = "application/json";
        context.Response.StatusCode = (int)code;

        return context.Response.WriteAsync(result);
    }
}

