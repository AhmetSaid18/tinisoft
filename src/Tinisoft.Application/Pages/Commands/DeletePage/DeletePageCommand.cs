using MediatR;

namespace Tinisoft.Application.Pages.Commands.DeletePage;

public class DeletePageCommand : IRequest<DeletePageResponse>
{
    public Guid PageId { get; set; }
}

public class DeletePageResponse
{
    public Guid PageId { get; set; }
    public string Message { get; set; } = "Sayfa başarıyla silindi.";
}

