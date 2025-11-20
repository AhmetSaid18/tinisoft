namespace Tinisoft.Application.Common.Exceptions;

public class ValidationException : Exception
{
    public ValidationException(string message) : base(message)
    {
        Errors = new Dictionary<string, string[]>();
    }

    public ValidationException(Dictionary<string, string[]> errors) 
        : base("Bir veya daha fazla doğrulama hatası oluştu.")
    {
        Errors = errors;
    }

    public Dictionary<string, string[]> Errors { get; }
}



