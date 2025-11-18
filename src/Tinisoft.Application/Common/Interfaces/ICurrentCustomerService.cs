namespace Tinisoft.Application.Common.Interfaces;

public interface ICurrentCustomerService
{
    Guid? GetCurrentCustomerId();
    bool IsCustomer();
}


