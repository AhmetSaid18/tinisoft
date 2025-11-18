using MediatR;

namespace Tinisoft.Application.Notifications.Queries.GetEmailTemplates;

public class GetEmailTemplatesQuery : IRequest<GetEmailTemplatesResponse>
{
    public bool? IsActive { get; set; }
}

public class GetEmailTemplatesResponse
{
    public List<EmailTemplateDto> Templates { get; set; } = new();
}

public class EmailTemplateDto
{
    public Guid Id { get; set; }
    public string TemplateCode { get; set; } = string.Empty;
    public string TemplateName { get; set; } = string.Empty;
    public string Subject { get; set; } = string.Empty;
    public bool IsActive { get; set; }
}

