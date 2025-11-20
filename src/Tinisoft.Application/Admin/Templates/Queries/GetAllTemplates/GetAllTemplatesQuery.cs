using MediatR;

namespace Tinisoft.Application.Admin.Templates.Queries.GetAllTemplates;

public class GetAllTemplatesQuery : IRequest<GetAllTemplatesResponse>
{
}

public class GetAllTemplatesResponse
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
    public DateTime CreatedAt { get; set; }
    public DateTime? UpdatedAt { get; set; }
    public int TenantCount { get; set; } // Bu template'i kaç tenant kullanıyor
}



