using MediatR;

namespace Tinisoft.Application.Admin.Templates.Commands.DeleteTemplate;

public class DeleteTemplateCommand : IRequest<DeleteTemplateResponse>
{
    public Guid TemplateId { get; set; }
}

public class DeleteTemplateResponse
{
    public Guid TemplateId { get; set; }
    public string Message { get; set; } = "Template başarıyla silindi.";
}



