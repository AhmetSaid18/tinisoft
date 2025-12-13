using MediatR;
using Tinisoft.Domain.Entities;

namespace Tinisoft.Application.Navigation.Queries.GetNavigation;

public class GetNavigationQuery : IRequest<GetNavigationResponse>
{
    public NavigationLocation? Location { get; set; }
    public bool OnlyVisible { get; set; } = true;
}

public class GetNavigationResponse
{
    public List<NavigationMenuDto> MenuItems { get; set; } = new();
}

public class NavigationMenuDto
{
    public Guid Id { get; set; }
    public string Title { get; set; } = string.Empty;
    public string? Url { get; set; }
    public string ItemType { get; set; } = "link";
    public Guid? PageId { get; set; }
    public Guid? CategoryId { get; set; }
    public Guid? ProductId { get; set; }
    public Guid? ParentId { get; set; }
    public string Location { get; set; } = "header";
    public int SortOrder { get; set; }
    public bool IsVisible { get; set; }
    public bool OpenInNewTab { get; set; }
    public string? Icon { get; set; }
    public string? CssClass { get; set; }
    
    // Alt menüler
    public List<NavigationMenuDto> Children { get; set; } = new();
}

