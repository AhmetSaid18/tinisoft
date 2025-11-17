using MediatR;
using Microsoft.EntityFrameworkCore;
using Tinisoft.Domain.Entities;
using Tinisoft.Infrastructure.Persistence;
using Finbuckle.MultiTenant;
using System.Security.Cryptography;
using System.Text;

namespace Tinisoft.Application.Auth.Commands.CreateApiKey;

public class CreateApiKeyCommandHandler : IRequestHandler<CreateApiKeyCommand, CreateApiKeyResponse>
{
    private readonly ApplicationDbContext _dbContext;
    private readonly IMultiTenantContextAccessor _tenantAccessor;
    private readonly ILogger<CreateApiKeyCommandHandler> _logger;

    public CreateApiKeyCommandHandler(
        ApplicationDbContext dbContext,
        IMultiTenantContextAccessor tenantAccessor,
        ILogger<CreateApiKeyCommandHandler> logger)
    {
        _dbContext = dbContext;
        _tenantAccessor = tenantAccessor;
        _logger = logger;
    }

    public async Task<CreateApiKeyResponse> Handle(CreateApiKeyCommand request, CancellationToken cancellationToken)
    {
        var tenantId = Guid.Parse(_tenantAccessor.MultiTenantContext!.TenantInfo!.Id!);

        // API Key oluştur
        var rawKey = GenerateApiKey();
        var keyPrefix = rawKey.Substring(0, 8);
        var hashedKey = HashApiKey(rawKey);

        var apiKey = new ApiKey
        {
            TenantId = tenantId,
            Name = request.Name,
            Key = hashedKey,
            KeyPrefix = keyPrefix,
            ExpiresAt = request.ExpiresAt,
            Permissions = request.Permissions,
            IsActive = true
        };

        _dbContext.Set<ApiKey>().Add(apiKey);
        await _dbContext.SaveChangesAsync(cancellationToken);

        _logger.LogInformation("API Key created: {Name} - {Prefix}", request.Name, keyPrefix);

        return new CreateApiKeyResponse
        {
            ApiKeyId = apiKey.Id,
            Key = rawKey, // Sadece bir kez gösterilir
            KeyPrefix = keyPrefix
        };
    }

    private static string GenerateApiKey()
    {
        return $"tinisoft_{Guid.NewGuid():N}";
    }

    private static string HashApiKey(string key)
    {
        using var sha256 = SHA256.Create();
        var hashBytes = sha256.ComputeHash(Encoding.UTF8.GetBytes(key));
        return Convert.ToBase64String(hashBytes);
    }
}

