using MediatR;

namespace Tinisoft.Application.Admin.Templates.Commands.CreateTemplate;

public class CreateTemplateCommand : IRequest<CreateTemplateResponse>
{
    public string Code { get; set; } = string.Empty; // "minimal", "fashion", etc.
    public string Name { get; set; } = string.Empty;
    public string Description { get; set; } = string.Empty;
    public int Version { get; set; } = 1;
    public string? PreviewImageUrl { get; set; }
    public bool IsActive { get; set; } = true;
    public Dictionary<string, object>? Metadata { get; set; } // Template metadata (JSON)
}

public class CreateTemplateResponse
{
    public Guid TemplateId { get; set; }
    public string Code { get; set; } = string.Empty;
    public string Name { get; set; } = string.Empty;
    public string Message { get; set; } = "Template başarıyla oluşturuldu.";
}



