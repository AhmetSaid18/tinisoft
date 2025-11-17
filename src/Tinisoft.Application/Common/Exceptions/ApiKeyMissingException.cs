namespace Tinisoft.Application.Common.Exceptions;

public class ApiKeyMissingException : Exception
{
    public ApiKeyMissingException(string marketplace) 
        : base($"{marketplace} entegrasyonu için API anahtarı girilmemiş. Lütfen API anahtarınızı girin.")
    {
        Marketplace = marketplace;
    }

    public string Marketplace { get; }
}

