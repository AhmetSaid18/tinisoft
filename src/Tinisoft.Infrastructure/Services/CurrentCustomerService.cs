using System.IdentityModel.Tokens.Jwt;
using System.Security.Claims;
using Microsoft.AspNetCore.Http;
using Tinisoft.Application.Common.Interfaces;

namespace Tinisoft.Infrastructure.Services;

public class CurrentCustomerService : ICurrentCustomerService
{
    private readonly IHttpContextAccessor _httpContextAccessor;

    public CurrentCustomerService(IHttpContextAccessor httpContextAccessor)
    {
        _httpContextAccessor = httpContextAccessor;
    }

    public Guid? GetCurrentCustomerId()
    {
        var httpContext = _httpContextAccessor.HttpContext;
        if (httpContext == null)
        {
            return null;
        }

        var role = httpContext.User.FindFirst("systemRole")?.Value;
        if (!string.Equals(role, "Customer", StringComparison.OrdinalIgnoreCase))
        {
            return null;
        }

        var idClaim = httpContext.User.FindFirst(ClaimTypes.NameIdentifier)
                      ?? httpContext.User.FindFirst(ClaimTypes.Name)
                      ?? httpContext.User.FindFirst(JwtRegisteredClaimNames.Sub)
                      ?? httpContext.User.FindFirst("sub");

        if (idClaim != null && Guid.TryParse(idClaim.Value, out var customerId))
        {
            return customerId;
        }

        return null;
    }

    public bool IsCustomer()
    {
        var httpContext = _httpContextAccessor.HttpContext;
        if (httpContext == null)
        {
            return false;
        }

        var role = httpContext.User.FindFirst("systemRole")?.Value;
        return role == "Customer";
    }
}


