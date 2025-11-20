namespace Tinisoft.Application.Common.Exceptions;

public class UnauthorizedException : Exception
{
    public UnauthorizedException(string message = "Bu işlem için yetkiniz bulunmamaktadır.") 
        : base(message)
    {
    }
}



