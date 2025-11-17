using MediatR;

namespace Tinisoft.Application.Templates.Queries.GetAvailableTemplates;

public class GetAvailableTemplatesQuery : IRequest<GetAvailableTemplatesResponse>
{
}

public class GetAvailableTemplatesResponse
{
    public List<TemplateDto> Templates { get; set; } = new();
}

public class TemplateDto
{
    public Guid Id { get; set; }
    public string Code { get; set; } = string.Empty;
    public string Name { get; set; } = string.Empty;
    public string Description { get; set; } = string.Empty;
    public int Version { get; set; }
    public string? PreviewImageUrl { get; set; }
    public bool IsActive { get; set; }
}

