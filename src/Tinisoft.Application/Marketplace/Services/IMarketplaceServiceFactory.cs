namespace Tinisoft.Application.Marketplace.Services;

public interface IMarketplaceServiceFactory
{
    IMarketplaceService GetService(string marketplace);
}

