using MediatR;

namespace Tinisoft.Application.Notifications.Commands.CreateEmailTemplate;

public class CreateEmailTemplateCommand : IRequest<CreateEmailTemplateResponse>
{
    public string TemplateCode { get; set; } = string.Empty; // "ORDER_CONFIRMATION", "ORDER_SHIPPED", vb.
    public string TemplateName { get; set; } = string.Empty;
    public string Subject { get; set; } = string.Empty;
    public string BodyHtml { get; set; } = string.Empty;
    public string? BodyText { get; set; }
}

public class CreateEmailTemplateResponse
{
    public Guid EmailTemplateId { get; set; }
    public string TemplateCode { get; set; } = string.Empty;
    public string TemplateName { get; set; } = string.Empty;
}

