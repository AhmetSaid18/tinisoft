namespace Tinisoft.Domain.Enums;

public enum NotificationType
{
    // Order related
    OrderConfirmation = 1,
    OrderStatusChanged = 2,
    OrderShipped = 3,
    OrderDelivered = 4,
    OrderCancelled = 5,
    
    // Customer related
    WelcomeEmail = 10,
    PasswordReset = 11,
    EmailVerification = 12,
    
    // Cart related
    AbandonedCart = 20,
    
    // Inventory related
    LowStockAlert = 30,
    OutOfStockAlert = 31,
    ProductBackInStock = 32,
    
    // Marketing
    CampaignEmail = 40,
    Newsletter = 41,
    
    // Admin alerts
    NewOrderAlert = 50,
    PaymentFailedAlert = 51
}

