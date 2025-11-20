using MediatR;

namespace Tinisoft.Application.Templates.Queries.GetSelectedTemplate;

public class GetSelectedTemplateQuery : IRequest<GetSelectedTemplateResponse>
{
}

public class GetSelectedTemplateResponse
{
    public string? TemplateCode { get; set; }
    public int? TemplateVersion { get; set; }
    public DateTime? SelectedAt { get; set; }
    public bool IsTemplateSelected => !string.IsNullOrWhiteSpace(TemplateCode);
}



