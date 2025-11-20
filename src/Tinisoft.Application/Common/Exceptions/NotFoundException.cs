namespace Tinisoft.Application.Common.Exceptions;

public class NotFoundException : Exception
{
    public NotFoundException(string resourceName, object? key = null)
        : base(key != null 
            ? $"{resourceName} (ID: {key}) bulunamadı." 
            : $"{resourceName} bulunamadı.")
    {
        ResourceName = resourceName;
        Key = key;
    }

    public string ResourceName { get; }
    public object? Key { get; }
}



