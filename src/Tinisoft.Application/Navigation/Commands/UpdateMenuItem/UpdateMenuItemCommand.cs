using MediatR;
using Tinisoft.Domain.Entities;

namespace Tinisoft.Application.Navigation.Commands.UpdateMenuItem;

public class UpdateMenuItemCommand : IRequest<UpdateMenuItemResponse>
{
    public Guid MenuItemId { get; set; }
    public string Title { get; set; } = string.Empty;
    public string? Url { get; set; }
    public NavigationItemType ItemType { get; set; }
    
    // İlişkili öğe
    public Guid? PageId { get; set; }
    public Guid? CategoryId { get; set; }
    public Guid? ProductId { get; set; }
    
    // Hiyerarşi
    public Guid? ParentId { get; set; }
    
    // Konum
    public NavigationLocation Location { get; set; }
    
    // Sıralama
    public int SortOrder { get; set; }
    
    // Görünürlük
    public bool IsVisible { get; set; }
    
    // Stil
    public bool OpenInNewTab { get; set; }
    public string? Icon { get; set; }
    public string? CssClass { get; set; }
}

public class UpdateMenuItemResponse
{
    public Guid MenuItemId { get; set; }
    public string Title { get; set; } = string.Empty;
    public string Message { get; set; } = "Menü öğesi başarıyla güncellendi.";
}

