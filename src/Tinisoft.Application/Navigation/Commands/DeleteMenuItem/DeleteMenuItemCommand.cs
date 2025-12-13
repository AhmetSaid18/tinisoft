using MediatR;

namespace Tinisoft.Application.Navigation.Commands.DeleteMenuItem;

public class DeleteMenuItemCommand : IRequest<DeleteMenuItemResponse>
{
    public Guid MenuItemId { get; set; }
}

public class DeleteMenuItemResponse
{
    public Guid MenuItemId { get; set; }
    public string Message { get; set; } = "Menü öğesi başarıyla silindi.";
}

