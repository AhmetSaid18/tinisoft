namespace Tinisoft.Application.Common.Exceptions;

public class MarketplaceIntegrationNotFoundException : Exception
{
    public MarketplaceIntegrationNotFoundException(string marketplace) 
        : base($"{marketplace} entegrasyonu bulunamadı veya aktif değil. Lütfen önce entegrasyonu yapılandırın.")
    {
        Marketplace = marketplace;
    }

    public string Marketplace { get; }
}

