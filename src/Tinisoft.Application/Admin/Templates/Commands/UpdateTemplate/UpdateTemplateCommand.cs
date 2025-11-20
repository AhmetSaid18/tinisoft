using MediatR;

namespace Tinisoft.Application.Admin.Templates.Commands.UpdateTemplate;

public class UpdateTemplateCommand : IRequest<UpdateTemplateResponse>
{
    public Guid TemplateId { get; set; }
    public string? Name { get; set; }
    public string? Description { get; set; }
    public string? PreviewImageUrl { get; set; }
    public bool? IsActive { get; set; }
    public Dictionary<string, object>? Metadata { get; set; }
}

public class UpdateTemplateResponse
{
    public Guid TemplateId { get; set; }
    public string Code { get; set; } = string.Empty;
    public string Message { get; set; } = "Template başarıyla güncellendi.";
}



