using MediatR;

namespace Tinisoft.Application.Auth.Commands.CreateApiKey;

public class CreateApiKeyCommand : IRequest<CreateApiKeyResponse>
{
    public string Name { get; set; } = string.Empty;
    public DateTime? ExpiresAt { get; set; }
    public List<string> Permissions { get; set; } = new(); // products:read, orders:write, etc.
}

public class CreateApiKeyResponse
{
    public Guid ApiKeyId { get; set; }
    public string Key { get; set; } = string.Empty; // Sadece bir kez gösterilir
    public string KeyPrefix { get; set; } = string.Empty;
}



