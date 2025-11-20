using System.Security.Claims;

namespace Tinisoft.Application.Common.Interfaces;

public interface IJwtTokenService
{
    string GenerateToken(Guid userId, string email, string systemRole, Guid? tenantId = null, string? tenantRole = null);
    ClaimsPrincipal? ValidateToken(string token);
}
