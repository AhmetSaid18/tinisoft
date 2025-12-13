using MediatR;
using Tinisoft.Domain.Entities;

namespace Tinisoft.Application.Navigation.Commands.CreateMenuItem;

public class CreateMenuItemCommand : IRequest<CreateMenuItemResponse>
{
    public string Title { get; set; } = string.Empty;
    public string? Url { get; set; }
    public NavigationItemType ItemType { get; set; } = NavigationItemType.Link;
    
    // İlişkili öğe
    public Guid? PageId { get; set; }
    public Guid? CategoryId { get; set; }
    public Guid? ProductId { get; set; }
    
    // Hiyerarşi
    public Guid? ParentId { get; set; }
    
    // Konum
    public NavigationLocation Location { get; set; } = NavigationLocation.Header;
    
    // Sıralama
    public int SortOrder { get; set; } = 0;
    
    // Stil
    public bool OpenInNewTab { get; set; } = false;
    public string? Icon { get; set; }
    public string? CssClass { get; set; }
}

public class CreateMenuItemResponse
{
    public Guid MenuItemId { get; set; }
    public string Title { get; set; } = string.Empty;
    public string Message { get; set; } = "Menü öğesi başarıyla oluşturuldu.";
}

