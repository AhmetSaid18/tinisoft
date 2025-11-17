using MediatR;

namespace Tinisoft.Application.Admin.Templates.Commands.ToggleTemplateActive;

public class ToggleTemplateActiveCommand : IRequest<ToggleTemplateActiveResponse>
{
    public Guid TemplateId { get; set; }
    public bool IsActive { get; set; }
}

public class ToggleTemplateActiveResponse
{
    public Guid TemplateId { get; set; }
    public bool IsActive { get; set; }
    public string Message { get; set; } = string.Empty;
}

