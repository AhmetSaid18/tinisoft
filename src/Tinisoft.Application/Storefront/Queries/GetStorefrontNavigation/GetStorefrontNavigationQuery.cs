using MediatR;

namespace Tinisoft.Application.Storefront.Queries.GetStorefrontNavigation;

public class GetStorefrontNavigationQuery : IRequest<GetStorefrontNavigationResponse>
{
}

public class GetStorefrontNavigationResponse
{
    public List<StorefrontMenuItemDto> Header { get; set; } = new();
    public List<StorefrontMenuItemDto> Footer { get; set; } = new();
    public List<StorefrontMenuItemDto> Mobile { get; set; } = new();
}

public class StorefrontMenuItemDto
{
    public string Title { get; set; } = string.Empty;
    public string Url { get; set; } = string.Empty;
    public bool OpenInNewTab { get; set; }
    public string? Icon { get; set; }
    public List<StorefrontMenuItemDto> Children { get; set; } = new();
}

