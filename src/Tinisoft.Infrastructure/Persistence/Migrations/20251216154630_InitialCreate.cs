using System;
using System.Collections.Generic;
using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace Tinisoft.Infrastructure.Migrations
{
    /// <inheritdoc />
    public partial class InitialCreate : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.EnsureSchema(
                name: "products");

            migrationBuilder.CreateTable(
                name: "Plans",
                schema: "products",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    Name = table.Column<string>(type: "text", nullable: false),
                    Description = table.Column<string>(type: "text", nullable: false),
                    MonthlyPrice = table.Column<decimal>(type: "numeric", nullable: false),
                    YearlyPrice = table.Column<decimal>(type: "numeric", nullable: false),
                    MaxProducts = table.Column<int>(type: "integer", nullable: false),
                    MaxOrdersPerMonth = table.Column<int>(type: "integer", nullable: false),
                    MaxStorageGB = table.Column<int>(type: "integer", nullable: false),
                    CustomDomainEnabled = table.Column<bool>(type: "boolean", nullable: false),
                    AdvancedAnalytics = table.Column<bool>(type: "boolean", nullable: false),
                    IsActive = table.Column<bool>(type: "boolean", nullable: false),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Plans", x => x.Id);
                });

            migrationBuilder.CreateTable(
                name: "Templates",
                schema: "products",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    Code = table.Column<string>(type: "text", nullable: false),
                    Name = table.Column<string>(type: "text", nullable: false),
                    Description = table.Column<string>(type: "text", nullable: false),
                    Version = table.Column<int>(type: "integer", nullable: false),
                    PreviewImageUrl = table.Column<string>(type: "text", nullable: true),
                    IsActive = table.Column<bool>(type: "boolean", nullable: false),
                    MetadataJson = table.Column<string>(type: "text", nullable: true),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Templates", x => x.Id);
                });

            migrationBuilder.CreateTable(
                name: "Users",
                schema: "products",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    Email = table.Column<string>(type: "text", nullable: false),
                    PasswordHash = table.Column<string>(type: "text", nullable: false),
                    FirstName = table.Column<string>(type: "text", nullable: true),
                    LastName = table.Column<string>(type: "text", nullable: true),
                    IsActive = table.Column<bool>(type: "boolean", nullable: false),
                    EmailVerified = table.Column<bool>(type: "boolean", nullable: false),
                    SystemRole = table.Column<string>(type: "text", nullable: false),
                    TwoFactorEnabled = table.Column<bool>(type: "boolean", nullable: false),
                    TwoFactorSecret = table.Column<string>(type: "text", nullable: true),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Users", x => x.Id);
                });

            migrationBuilder.CreateTable(
                name: "Tenants",
                schema: "products",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    Name = table.Column<string>(type: "text", nullable: false),
                    Slug = table.Column<string>(type: "text", nullable: false),
                    IsActive = table.Column<bool>(type: "boolean", nullable: false),
                    PlanId = table.Column<Guid>(type: "uuid", nullable: false),
                    SubscriptionStartDate = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    SubscriptionEndDate = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    PayTRSubscriptionToken = table.Column<string>(type: "text", nullable: true),
                    FacebookUrl = table.Column<string>(type: "text", nullable: true),
                    InstagramUrl = table.Column<string>(type: "text", nullable: true),
                    TwitterUrl = table.Column<string>(type: "text", nullable: true),
                    LinkedInUrl = table.Column<string>(type: "text", nullable: true),
                    YouTubeUrl = table.Column<string>(type: "text", nullable: true),
                    TikTokUrl = table.Column<string>(type: "text", nullable: true),
                    PinterestUrl = table.Column<string>(type: "text", nullable: true),
                    WhatsAppNumber = table.Column<string>(type: "text", nullable: true),
                    TelegramUsername = table.Column<string>(type: "text", nullable: true),
                    Email = table.Column<string>(type: "text", nullable: true),
                    Phone = table.Column<string>(type: "text", nullable: true),
                    Address = table.Column<string>(type: "text", nullable: true),
                    City = table.Column<string>(type: "text", nullable: true),
                    Country = table.Column<string>(type: "text", nullable: true),
                    LogoUrl = table.Column<string>(type: "text", nullable: true),
                    FaviconUrl = table.Column<string>(type: "text", nullable: true),
                    SiteTitle = table.Column<string>(type: "text", nullable: true),
                    SiteDescription = table.Column<string>(type: "text", nullable: true),
                    PrimaryColor = table.Column<string>(type: "text", nullable: true),
                    SecondaryColor = table.Column<string>(type: "text", nullable: true),
                    BackgroundColor = table.Column<string>(type: "text", nullable: true),
                    TextColor = table.Column<string>(type: "text", nullable: true),
                    LinkColor = table.Column<string>(type: "text", nullable: true),
                    ButtonColor = table.Column<string>(type: "text", nullable: true),
                    ButtonTextColor = table.Column<string>(type: "text", nullable: true),
                    FontFamily = table.Column<string>(type: "text", nullable: true),
                    HeadingFontFamily = table.Column<string>(type: "text", nullable: true),
                    BaseFontSize = table.Column<int>(type: "integer", nullable: true),
                    LayoutSettingsJson = table.Column<string>(type: "text", nullable: true),
                    SelectedTemplateCode = table.Column<string>(type: "text", nullable: true),
                    SelectedTemplateVersion = table.Column<int>(type: "integer", nullable: true),
                    TemplateSelectedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    BaseCurrency = table.Column<string>(type: "text", nullable: false),
                    PurchaseCurrency = table.Column<string>(type: "text", nullable: true),
                    SaleCurrency = table.Column<string>(type: "text", nullable: false),
                    CurrencyMarginPercent = table.Column<decimal>(type: "numeric", nullable: false),
                    AutoUpdateExchangeRates = table.Column<bool>(type: "boolean", nullable: false),
                    TemplateId = table.Column<Guid>(type: "uuid", nullable: true),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Tenants", x => x.Id);
                    table.ForeignKey(
                        name: "FK_Tenants_Plans_PlanId",
                        column: x => x.PlanId,
                        principalSchema: "products",
                        principalTable: "Plans",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_Tenants_Templates_TemplateId",
                        column: x => x.TemplateId,
                        principalSchema: "products",
                        principalTable: "Templates",
                        principalColumn: "Id");
                });

            migrationBuilder.CreateTable(
                name: "ApiKeys",
                schema: "products",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    TenantId = table.Column<Guid>(type: "uuid", nullable: false),
                    Name = table.Column<string>(type: "text", nullable: false),
                    Key = table.Column<string>(type: "text", nullable: false),
                    KeyPrefix = table.Column<string>(type: "text", nullable: false),
                    IsActive = table.Column<bool>(type: "boolean", nullable: false),
                    ExpiresAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    Permissions = table.Column<List<string>>(type: "text[]", nullable: false),
                    LastUsedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_ApiKeys", x => x.Id);
                    table.ForeignKey(
                        name: "FK_ApiKeys_Tenants_TenantId",
                        column: x => x.TenantId,
                        principalSchema: "products",
                        principalTable: "Tenants",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "AuditLogs",
                schema: "products",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    TenantId = table.Column<Guid>(type: "uuid", nullable: false),
                    UserId = table.Column<Guid>(type: "uuid", nullable: true),
                    Action = table.Column<string>(type: "text", nullable: false),
                    EntityType = table.Column<string>(type: "text", nullable: false),
                    EntityId = table.Column<Guid>(type: "uuid", nullable: false),
                    ChangesJson = table.Column<string>(type: "text", nullable: true),
                    IpAddress = table.Column<string>(type: "text", nullable: true),
                    UserAgent = table.Column<string>(type: "text", nullable: true),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_AuditLogs", x => x.Id);
                    table.ForeignKey(
                        name: "FK_AuditLogs_Tenants_TenantId",
                        column: x => x.TenantId,
                        principalSchema: "products",
                        principalTable: "Tenants",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_AuditLogs_Users_UserId",
                        column: x => x.UserId,
                        principalSchema: "products",
                        principalTable: "Users",
                        principalColumn: "Id");
                });

            migrationBuilder.CreateTable(
                name: "Categories",
                schema: "products",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    TenantId = table.Column<Guid>(type: "uuid", nullable: false),
                    Name = table.Column<string>(type: "text", nullable: false),
                    Slug = table.Column<string>(type: "text", nullable: false),
                    Description = table.Column<string>(type: "text", nullable: true),
                    ImageUrl = table.Column<string>(type: "text", nullable: true),
                    ParentCategoryId = table.Column<Guid>(type: "uuid", nullable: true),
                    DisplayOrder = table.Column<int>(type: "integer", nullable: false),
                    IsActive = table.Column<bool>(type: "boolean", nullable: false),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Categories", x => x.Id);
                    table.ForeignKey(
                        name: "FK_Categories_Categories_ParentCategoryId",
                        column: x => x.ParentCategoryId,
                        principalSchema: "products",
                        principalTable: "Categories",
                        principalColumn: "Id");
                    table.ForeignKey(
                        name: "FK_Categories_Tenants_TenantId",
                        column: x => x.TenantId,
                        principalSchema: "products",
                        principalTable: "Tenants",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "Coupons",
                schema: "products",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    TenantId = table.Column<Guid>(type: "uuid", nullable: false),
                    Code = table.Column<string>(type: "text", nullable: false),
                    Name = table.Column<string>(type: "text", nullable: false),
                    Description = table.Column<string>(type: "text", nullable: true),
                    DiscountType = table.Column<string>(type: "text", nullable: false),
                    DiscountValue = table.Column<decimal>(type: "numeric", nullable: false),
                    Currency = table.Column<string>(type: "text", nullable: false),
                    MinOrderAmount = table.Column<decimal>(type: "numeric", nullable: true),
                    MaxDiscountAmount = table.Column<decimal>(type: "numeric", nullable: true),
                    MaxUsageCount = table.Column<int>(type: "integer", nullable: true),
                    MaxUsagePerCustomer = table.Column<int>(type: "integer", nullable: true),
                    ValidFrom = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    ValidTo = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    AppliesToAllProducts = table.Column<bool>(type: "boolean", nullable: false),
                    AppliesToAllCustomers = table.Column<bool>(type: "boolean", nullable: false),
                    IsActive = table.Column<bool>(type: "boolean", nullable: false),
                    UsageCount = table.Column<int>(type: "integer", nullable: false),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Coupons", x => x.Id);
                    table.ForeignKey(
                        name: "FK_Coupons_Tenants_TenantId",
                        column: x => x.TenantId,
                        principalSchema: "products",
                        principalTable: "Tenants",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "Customers",
                schema: "products",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    TenantId = table.Column<Guid>(type: "uuid", nullable: false),
                    Email = table.Column<string>(type: "text", nullable: false),
                    PasswordHash = table.Column<string>(type: "text", nullable: false),
                    FirstName = table.Column<string>(type: "text", nullable: true),
                    LastName = table.Column<string>(type: "text", nullable: true),
                    Phone = table.Column<string>(type: "text", nullable: true),
                    EmailVerified = table.Column<bool>(type: "boolean", nullable: false),
                    LastLoginAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    IsActive = table.Column<bool>(type: "boolean", nullable: false),
                    DefaultShippingAddressId = table.Column<Guid>(type: "uuid", nullable: true),
                    DefaultBillingAddressId = table.Column<Guid>(type: "uuid", nullable: true),
                    ResetPasswordToken = table.Column<string>(type: "text", nullable: true),
                    ResetPasswordTokenExpiresAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Customers", x => x.Id);
                    table.ForeignKey(
                        name: "FK_Customers_Tenants_TenantId",
                        column: x => x.TenantId,
                        principalSchema: "products",
                        principalTable: "Tenants",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "Domains",
                schema: "products",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    TenantId = table.Column<Guid>(type: "uuid", nullable: false),
                    Host = table.Column<string>(type: "text", nullable: false),
                    IsPrimary = table.Column<bool>(type: "boolean", nullable: false),
                    IsVerified = table.Column<bool>(type: "boolean", nullable: false),
                    VerificationToken = table.Column<string>(type: "text", nullable: true),
                    VerifiedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    SslEnabled = table.Column<bool>(type: "boolean", nullable: false),
                    SslIssuedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    SslExpiresAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Domains", x => x.Id);
                    table.ForeignKey(
                        name: "FK_Domains_Tenants_TenantId",
                        column: x => x.TenantId,
                        principalSchema: "products",
                        principalTable: "Tenants",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "EmailProviders",
                schema: "products",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    TenantId = table.Column<Guid>(type: "uuid", nullable: false),
                    ProviderName = table.Column<string>(type: "text", nullable: false),
                    IsActive = table.Column<bool>(type: "boolean", nullable: false),
                    IsDefault = table.Column<bool>(type: "boolean", nullable: false),
                    SmtpHost = table.Column<string>(type: "text", nullable: false),
                    SmtpPort = table.Column<int>(type: "integer", nullable: false),
                    EnableSsl = table.Column<bool>(type: "boolean", nullable: false),
                    SmtpUsername = table.Column<string>(type: "text", nullable: false),
                    SmtpPassword = table.Column<string>(type: "text", nullable: false),
                    FromEmail = table.Column<string>(type: "text", nullable: false),
                    FromName = table.Column<string>(type: "text", nullable: false),
                    ReplyToEmail = table.Column<string>(type: "text", nullable: true),
                    SettingsJson = table.Column<string>(type: "text", nullable: true),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_EmailProviders", x => x.Id);
                    table.ForeignKey(
                        name: "FK_EmailProviders_Tenants_TenantId",
                        column: x => x.TenantId,
                        principalSchema: "products",
                        principalTable: "Tenants",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateTable(
                name: "EmailTemplates",
                schema: "products",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    TenantId = table.Column<Guid>(type: "uuid", nullable: false),
                    Type = table.Column<int>(type: "integer", nullable: false),
                    TemplateCode = table.Column<string>(type: "text", nullable: false),
                    TemplateName = table.Column<string>(type: "text", nullable: false),
                    Name = table.Column<string>(type: "text", nullable: false),
                    Subject = table.Column<string>(type: "text", nullable: false),
                    HtmlBody = table.Column<string>(type: "text", nullable: false),
                    BodyHtml = table.Column<string>(type: "text", nullable: false),
                    TextBody = table.Column<string>(type: "text", nullable: true),
                    BodyText = table.Column<string>(type: "text", nullable: true),
                    SmsBody = table.Column<string>(type: "text", nullable: true),
                    IsActive = table.Column<bool>(type: "boolean", nullable: false),
                    IsDefault = table.Column<bool>(type: "boolean", nullable: false),
                    AvailableVariables = table.Column<string>(type: "text", nullable: true),
                    Language = table.Column<string>(type: "text", nullable: false),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_EmailTemplates", x => x.Id);
                    table.ForeignKey(
                        name: "FK_EmailTemplates_Tenants_TenantId",
                        column: x => x.TenantId,
                        principalSchema: "products",
                        principalTable: "Tenants",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateTable(
                name: "MarketplaceIntegrations",
                schema: "products",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    TenantId = table.Column<Guid>(type: "uuid", nullable: false),
                    Marketplace = table.Column<string>(type: "text", nullable: false),
                    IsActive = table.Column<bool>(type: "boolean", nullable: false),
                    ApiKey = table.Column<string>(type: "text", nullable: true),
                    ApiSecret = table.Column<string>(type: "text", nullable: true),
                    SupplierId = table.Column<string>(type: "text", nullable: true),
                    UserId = table.Column<string>(type: "text", nullable: true),
                    AutoSyncProducts = table.Column<bool>(type: "boolean", nullable: false),
                    AutoSyncOrders = table.Column<bool>(type: "boolean", nullable: false),
                    AutoSyncInventory = table.Column<bool>(type: "boolean", nullable: false),
                    LastSyncAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    LastSyncStatus = table.Column<string>(type: "text", nullable: true),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_MarketplaceIntegrations", x => x.Id);
                    table.ForeignKey(
                        name: "FK_MarketplaceIntegrations_Tenants_TenantId",
                        column: x => x.TenantId,
                        principalSchema: "products",
                        principalTable: "Tenants",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "Pages",
                schema: "products",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    TenantId = table.Column<Guid>(type: "uuid", nullable: false),
                    Title = table.Column<string>(type: "text", nullable: false),
                    Slug = table.Column<string>(type: "text", nullable: false),
                    Content = table.Column<string>(type: "text", nullable: false),
                    MetaTitle = table.Column<string>(type: "text", nullable: true),
                    MetaDescription = table.Column<string>(type: "text", nullable: true),
                    MetaKeywords = table.Column<string>(type: "text", nullable: true),
                    CanonicalUrl = table.Column<string>(type: "text", nullable: true),
                    FeaturedImageUrl = table.Column<string>(type: "text", nullable: true),
                    IsPublished = table.Column<bool>(type: "boolean", nullable: false),
                    PublishedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    Template = table.Column<string>(type: "text", nullable: false),
                    SortOrder = table.Column<int>(type: "integer", nullable: false),
                    IsSystemPage = table.Column<bool>(type: "boolean", nullable: false),
                    SystemPageType = table.Column<string>(type: "text", nullable: true),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Pages", x => x.Id);
                    table.ForeignKey(
                        name: "FK_Pages_Tenants_TenantId",
                        column: x => x.TenantId,
                        principalSchema: "products",
                        principalTable: "Tenants",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "PaymentProviders",
                schema: "products",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    TenantId = table.Column<Guid>(type: "uuid", nullable: false),
                    ProviderCode = table.Column<string>(type: "text", nullable: false),
                    ProviderName = table.Column<string>(type: "text", nullable: false),
                    IsActive = table.Column<bool>(type: "boolean", nullable: false),
                    ApiKey = table.Column<string>(type: "text", nullable: true),
                    ApiSecret = table.Column<string>(type: "text", nullable: true),
                    ApiUrl = table.Column<string>(type: "text", nullable: true),
                    TestApiUrl = table.Column<string>(type: "text", nullable: true),
                    UseTestMode = table.Column<bool>(type: "boolean", nullable: false),
                    SettingsJson = table.Column<string>(type: "text", nullable: true),
                    IsDefault = table.Column<bool>(type: "boolean", nullable: false),
                    Priority = table.Column<int>(type: "integer", nullable: false),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_PaymentProviders", x => x.Id);
                    table.ForeignKey(
                        name: "FK_PaymentProviders_Tenants_TenantId",
                        column: x => x.TenantId,
                        principalSchema: "products",
                        principalTable: "Tenants",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateTable(
                name: "ProductTags",
                schema: "products",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    TenantId = table.Column<Guid>(type: "uuid", nullable: false),
                    Name = table.Column<string>(type: "text", nullable: false),
                    Slug = table.Column<string>(type: "text", nullable: false),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_ProductTags", x => x.Id);
                    table.ForeignKey(
                        name: "FK_ProductTags_Tenants_TenantId",
                        column: x => x.TenantId,
                        principalSchema: "products",
                        principalTable: "Tenants",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "Resellers",
                schema: "products",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    TenantId = table.Column<Guid>(type: "uuid", nullable: false),
                    CompanyName = table.Column<string>(type: "text", nullable: false),
                    TaxNumber = table.Column<string>(type: "text", nullable: true),
                    TaxOffice = table.Column<string>(type: "text", nullable: true),
                    Email = table.Column<string>(type: "text", nullable: false),
                    Phone = table.Column<string>(type: "text", nullable: true),
                    Mobile = table.Column<string>(type: "text", nullable: true),
                    Address = table.Column<string>(type: "text", nullable: true),
                    City = table.Column<string>(type: "text", nullable: true),
                    State = table.Column<string>(type: "text", nullable: true),
                    PostalCode = table.Column<string>(type: "text", nullable: true),
                    Country = table.Column<string>(type: "text", nullable: true),
                    ContactPersonName = table.Column<string>(type: "text", nullable: true),
                    ContactPersonTitle = table.Column<string>(type: "text", nullable: true),
                    IsActive = table.Column<bool>(type: "boolean", nullable: false),
                    ApprovedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    ApprovedByUserId = table.Column<Guid>(type: "uuid", nullable: true),
                    CreditLimit = table.Column<decimal>(type: "numeric", nullable: false),
                    UsedCredit = table.Column<decimal>(type: "numeric", nullable: false),
                    PaymentTermDays = table.Column<int>(type: "integer", nullable: false),
                    PaymentMethod = table.Column<string>(type: "text", nullable: false),
                    DefaultDiscountPercent = table.Column<decimal>(type: "numeric", nullable: false),
                    UseCustomPricing = table.Column<bool>(type: "boolean", nullable: false),
                    Notes = table.Column<string>(type: "text", nullable: true),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Resellers", x => x.Id);
                    table.ForeignKey(
                        name: "FK_Resellers_Tenants_TenantId",
                        column: x => x.TenantId,
                        principalSchema: "products",
                        principalTable: "Tenants",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "ShippingProviders",
                schema: "products",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    TenantId = table.Column<Guid>(type: "uuid", nullable: false),
                    ProviderCode = table.Column<string>(type: "text", nullable: false),
                    ProviderName = table.Column<string>(type: "text", nullable: false),
                    IsActive = table.Column<bool>(type: "boolean", nullable: false),
                    ApiKey = table.Column<string>(type: "text", nullable: true),
                    ApiSecret = table.Column<string>(type: "text", nullable: true),
                    ApiUrl = table.Column<string>(type: "text", nullable: true),
                    TestApiUrl = table.Column<string>(type: "text", nullable: true),
                    UseTestMode = table.Column<bool>(type: "boolean", nullable: false),
                    SettingsJson = table.Column<string>(type: "text", nullable: true),
                    IsDefault = table.Column<bool>(type: "boolean", nullable: false),
                    Priority = table.Column<int>(type: "integer", nullable: false),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_ShippingProviders", x => x.Id);
                    table.ForeignKey(
                        name: "FK_ShippingProviders_Tenants_TenantId",
                        column: x => x.TenantId,
                        principalSchema: "products",
                        principalTable: "Tenants",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateTable(
                name: "TaxRates",
                schema: "products",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    TenantId = table.Column<Guid>(type: "uuid", nullable: false),
                    Name = table.Column<string>(type: "text", nullable: false),
                    Code = table.Column<string>(type: "text", nullable: false),
                    Rate = table.Column<decimal>(type: "numeric", nullable: false),
                    Type = table.Column<string>(type: "text", nullable: false),
                    IsActive = table.Column<bool>(type: "boolean", nullable: false),
                    Description = table.Column<string>(type: "text", nullable: true),
                    TaxCode = table.Column<string>(type: "text", nullable: true),
                    ExciseTaxCode = table.Column<string>(type: "text", nullable: true),
                    ProductServiceCode = table.Column<string>(type: "text", nullable: true),
                    IsIncludedInPrice = table.Column<bool>(type: "boolean", nullable: false),
                    EInvoiceTaxType = table.Column<string>(type: "text", nullable: true),
                    IsExempt = table.Column<bool>(type: "boolean", nullable: false),
                    ExemptionReason = table.Column<string>(type: "text", nullable: true),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_TaxRates", x => x.Id);
                    table.ForeignKey(
                        name: "FK_TaxRates_Tenants_TenantId",
                        column: x => x.TenantId,
                        principalSchema: "products",
                        principalTable: "Tenants",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "TenantInvoiceSettings",
                schema: "products",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    TenantId = table.Column<Guid>(type: "uuid", nullable: false),
                    IsEFaturaUser = table.Column<bool>(type: "boolean", nullable: false),
                    VKN = table.Column<string>(type: "text", nullable: true),
                    TCKN = table.Column<string>(type: "text", nullable: true),
                    TaxOffice = table.Column<string>(type: "text", nullable: true),
                    TaxNumber = table.Column<string>(type: "text", nullable: true),
                    EFaturaAlias = table.Column<string>(type: "text", nullable: true),
                    EFaturaPassword = table.Column<string>(type: "text", nullable: true),
                    CompanyName = table.Column<string>(type: "text", nullable: true),
                    CompanyTitle = table.Column<string>(type: "text", nullable: true),
                    CompanyAddressLine1 = table.Column<string>(type: "text", nullable: true),
                    CompanyAddressLine2 = table.Column<string>(type: "text", nullable: true),
                    CompanyCity = table.Column<string>(type: "text", nullable: true),
                    CompanyState = table.Column<string>(type: "text", nullable: true),
                    CompanyPostalCode = table.Column<string>(type: "text", nullable: true),
                    CompanyCountry = table.Column<string>(type: "text", nullable: true),
                    CompanyPhone = table.Column<string>(type: "text", nullable: true),
                    CompanyEmail = table.Column<string>(type: "text", nullable: true),
                    CompanyWebsite = table.Column<string>(type: "text", nullable: true),
                    BankName = table.Column<string>(type: "text", nullable: true),
                    BankBranch = table.Column<string>(type: "text", nullable: true),
                    IBAN = table.Column<string>(type: "text", nullable: true),
                    AccountName = table.Column<string>(type: "text", nullable: true),
                    MaliMuhurCertificateBase64 = table.Column<string>(type: "text", nullable: true),
                    MaliMuhurPassword = table.Column<string>(type: "text", nullable: true),
                    MaliMuhurSerialNumber = table.Column<string>(type: "text", nullable: true),
                    MaliMuhurExpiryDate = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    InvoicePrefix = table.Column<string>(type: "text", nullable: false),
                    InvoiceSerial = table.Column<string>(type: "text", nullable: false),
                    InvoiceStartNumber = table.Column<int>(type: "integer", nullable: false),
                    LastInvoiceNumber = table.Column<int>(type: "integer", nullable: false),
                    DefaultInvoiceType = table.Column<string>(type: "text", nullable: false),
                    DefaultProfileId = table.Column<string>(type: "text", nullable: false),
                    PaymentDueDays = table.Column<int>(type: "integer", nullable: false),
                    AutoCreateInvoiceOnOrderPaid = table.Column<bool>(type: "boolean", nullable: false),
                    AutoSendToGIB = table.Column<bool>(type: "boolean", nullable: false),
                    UseTestEnvironment = table.Column<bool>(type: "boolean", nullable: false),
                    GIBTestVKN = table.Column<string>(type: "text", nullable: true),
                    GIBTestAlias = table.Column<string>(type: "text", nullable: true),
                    IsActive = table.Column<bool>(type: "boolean", nullable: false),
                    LastInvoiceSyncAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_TenantInvoiceSettings", x => x.Id);
                    table.ForeignKey(
                        name: "FK_TenantInvoiceSettings_Tenants_TenantId",
                        column: x => x.TenantId,
                        principalSchema: "products",
                        principalTable: "Tenants",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateTable(
                name: "UserTenantRoles",
                schema: "products",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    UserId = table.Column<Guid>(type: "uuid", nullable: false),
                    TenantId = table.Column<Guid>(type: "uuid", nullable: false),
                    Role = table.Column<string>(type: "text", nullable: false),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_UserTenantRoles", x => x.Id);
                    table.ForeignKey(
                        name: "FK_UserTenantRoles_Tenants_TenantId",
                        column: x => x.TenantId,
                        principalSchema: "products",
                        principalTable: "Tenants",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_UserTenantRoles_Users_UserId",
                        column: x => x.UserId,
                        principalSchema: "products",
                        principalTable: "Users",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "Warehouses",
                schema: "products",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    TenantId = table.Column<Guid>(type: "uuid", nullable: false),
                    Name = table.Column<string>(type: "text", nullable: false),
                    Address = table.Column<string>(type: "text", nullable: true),
                    City = table.Column<string>(type: "text", nullable: true),
                    Country = table.Column<string>(type: "text", nullable: true),
                    IsDefault = table.Column<bool>(type: "boolean", nullable: false),
                    IsActive = table.Column<bool>(type: "boolean", nullable: false),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Warehouses", x => x.Id);
                    table.ForeignKey(
                        name: "FK_Warehouses_Tenants_TenantId",
                        column: x => x.TenantId,
                        principalSchema: "products",
                        principalTable: "Tenants",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "Webhooks",
                schema: "products",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    TenantId = table.Column<Guid>(type: "uuid", nullable: false),
                    Url = table.Column<string>(type: "text", nullable: false),
                    Secret = table.Column<string>(type: "text", nullable: false),
                    Events = table.Column<List<string>>(type: "text[]", nullable: false),
                    IsActive = table.Column<bool>(type: "boolean", nullable: false),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Webhooks", x => x.Id);
                    table.ForeignKey(
                        name: "FK_Webhooks_Tenants_TenantId",
                        column: x => x.TenantId,
                        principalSchema: "products",
                        principalTable: "Tenants",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "CouponCategories",
                schema: "products",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    CouponId = table.Column<Guid>(type: "uuid", nullable: false),
                    CategoryId = table.Column<Guid>(type: "uuid", nullable: false),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_CouponCategories", x => x.Id);
                    table.ForeignKey(
                        name: "FK_CouponCategories_Categories_CategoryId",
                        column: x => x.CategoryId,
                        principalSchema: "products",
                        principalTable: "Categories",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_CouponCategories_Coupons_CouponId",
                        column: x => x.CouponId,
                        principalSchema: "products",
                        principalTable: "Coupons",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "Carts",
                schema: "products",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    TenantId = table.Column<Guid>(type: "uuid", nullable: false),
                    CustomerId = table.Column<Guid>(type: "uuid", nullable: false),
                    CouponCode = table.Column<string>(type: "text", nullable: true),
                    CouponId = table.Column<Guid>(type: "uuid", nullable: true),
                    Subtotal = table.Column<decimal>(type: "numeric", nullable: false),
                    Tax = table.Column<decimal>(type: "numeric", nullable: false),
                    Shipping = table.Column<decimal>(type: "numeric", nullable: false),
                    Discount = table.Column<decimal>(type: "numeric", nullable: false),
                    Total = table.Column<decimal>(type: "numeric", nullable: false),
                    Currency = table.Column<string>(type: "text", nullable: false),
                    ExpiresAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    LastUpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Carts", x => x.Id);
                    table.ForeignKey(
                        name: "FK_Carts_Coupons_CouponId",
                        column: x => x.CouponId,
                        principalSchema: "products",
                        principalTable: "Coupons",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.SetNull);
                    table.ForeignKey(
                        name: "FK_Carts_Customers_CustomerId",
                        column: x => x.CustomerId,
                        principalSchema: "products",
                        principalTable: "Customers",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_Carts_Tenants_TenantId",
                        column: x => x.TenantId,
                        principalSchema: "products",
                        principalTable: "Tenants",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "CouponCustomers",
                schema: "products",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    CouponId = table.Column<Guid>(type: "uuid", nullable: false),
                    CustomerId = table.Column<Guid>(type: "uuid", nullable: false),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_CouponCustomers", x => x.Id);
                    table.ForeignKey(
                        name: "FK_CouponCustomers_Coupons_CouponId",
                        column: x => x.CouponId,
                        principalSchema: "products",
                        principalTable: "Coupons",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_CouponCustomers_Customers_CustomerId",
                        column: x => x.CustomerId,
                        principalSchema: "products",
                        principalTable: "Customers",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateTable(
                name: "CustomerAddresses",
                schema: "products",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    TenantId = table.Column<Guid>(type: "uuid", nullable: false),
                    CustomerId = table.Column<Guid>(type: "uuid", nullable: false),
                    AddressLine1 = table.Column<string>(type: "text", nullable: false),
                    AddressLine2 = table.Column<string>(type: "text", nullable: true),
                    City = table.Column<string>(type: "text", nullable: false),
                    State = table.Column<string>(type: "text", nullable: true),
                    PostalCode = table.Column<string>(type: "text", nullable: false),
                    Country = table.Column<string>(type: "text", nullable: false),
                    Phone = table.Column<string>(type: "text", nullable: true),
                    IsDefaultShipping = table.Column<bool>(type: "boolean", nullable: false),
                    IsDefaultBilling = table.Column<bool>(type: "boolean", nullable: false),
                    AddressTitle = table.Column<string>(type: "text", nullable: true),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_CustomerAddresses", x => x.Id);
                    table.ForeignKey(
                        name: "FK_CustomerAddresses_Customers_CustomerId",
                        column: x => x.CustomerId,
                        principalSchema: "products",
                        principalTable: "Customers",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_CustomerAddresses_Tenants_TenantId",
                        column: x => x.TenantId,
                        principalSchema: "products",
                        principalTable: "Tenants",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "EmailNotifications",
                schema: "products",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    TenantId = table.Column<Guid>(type: "uuid", nullable: false),
                    EmailProviderId = table.Column<Guid>(type: "uuid", nullable: true),
                    EmailTemplateId = table.Column<Guid>(type: "uuid", nullable: true),
                    ToEmail = table.Column<string>(type: "text", nullable: false),
                    ToName = table.Column<string>(type: "text", nullable: true),
                    CcEmail = table.Column<string>(type: "text", nullable: true),
                    BccEmail = table.Column<string>(type: "text", nullable: true),
                    Subject = table.Column<string>(type: "text", nullable: false),
                    BodyHtml = table.Column<string>(type: "text", nullable: false),
                    BodyText = table.Column<string>(type: "text", nullable: true),
                    Status = table.Column<string>(type: "text", nullable: false),
                    SentAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    ErrorMessage = table.Column<string>(type: "text", nullable: true),
                    ReferenceId = table.Column<Guid>(type: "uuid", nullable: true),
                    ReferenceType = table.Column<string>(type: "text", nullable: true),
                    ProviderResponseJson = table.Column<string>(type: "text", nullable: true),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_EmailNotifications", x => x.Id);
                    table.ForeignKey(
                        name: "FK_EmailNotifications_EmailProviders_EmailProviderId",
                        column: x => x.EmailProviderId,
                        principalSchema: "products",
                        principalTable: "EmailProviders",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.SetNull);
                    table.ForeignKey(
                        name: "FK_EmailNotifications_EmailTemplates_EmailTemplateId",
                        column: x => x.EmailTemplateId,
                        principalSchema: "products",
                        principalTable: "EmailTemplates",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.SetNull);
                    table.ForeignKey(
                        name: "FK_EmailNotifications_Tenants_TenantId",
                        column: x => x.TenantId,
                        principalSchema: "products",
                        principalTable: "Tenants",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "Products",
                schema: "products",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    TenantId = table.Column<Guid>(type: "uuid", nullable: false),
                    Title = table.Column<string>(type: "text", nullable: false),
                    Description = table.Column<string>(type: "text", nullable: true),
                    ShortDescription = table.Column<string>(type: "text", nullable: true),
                    Slug = table.Column<string>(type: "text", nullable: false),
                    SKU = table.Column<string>(type: "text", nullable: true),
                    Barcode = table.Column<string>(type: "text", nullable: true),
                    GTIN = table.Column<string>(type: "text", nullable: true),
                    Price = table.Column<decimal>(type: "numeric", nullable: false),
                    CompareAtPrice = table.Column<decimal>(type: "numeric", nullable: true),
                    CostPerItem = table.Column<decimal>(type: "numeric", nullable: false),
                    Currency = table.Column<string>(type: "text", nullable: false),
                    PurchaseCurrency = table.Column<string>(type: "text", nullable: true),
                    PurchasePrice = table.Column<decimal>(type: "numeric", nullable: true),
                    AutoConvertSalePrice = table.Column<bool>(type: "boolean", nullable: false),
                    ExchangeRateAtPurchase = table.Column<decimal>(type: "numeric", nullable: true),
                    Status = table.Column<string>(type: "text", nullable: false),
                    IsActive = table.Column<bool>(type: "boolean", nullable: false),
                    PublishedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    TrackInventory = table.Column<bool>(type: "boolean", nullable: false),
                    InventoryQuantity = table.Column<int>(type: "integer", nullable: true),
                    AllowBackorder = table.Column<bool>(type: "boolean", nullable: false),
                    InventoryPolicy = table.Column<string>(type: "text", nullable: false),
                    Weight = table.Column<decimal>(type: "numeric", nullable: true),
                    WeightUnit = table.Column<string>(type: "text", nullable: true),
                    Length = table.Column<decimal>(type: "numeric", nullable: true),
                    Width = table.Column<decimal>(type: "numeric", nullable: true),
                    Height = table.Column<decimal>(type: "numeric", nullable: true),
                    ShippingWeight = table.Column<decimal>(type: "numeric", nullable: true),
                    ShippingClass = table.Column<string>(type: "text", nullable: true),
                    IsTaxable = table.Column<bool>(type: "boolean", nullable: false),
                    TaxCode = table.Column<string>(type: "text", nullable: true),
                    MetaTitle = table.Column<string>(type: "text", nullable: true),
                    MetaDescription = table.Column<string>(type: "text", nullable: true),
                    MetaKeywords = table.Column<string>(type: "text", nullable: true),
                    OgTitle = table.Column<string>(type: "text", nullable: true),
                    OgDescription = table.Column<string>(type: "text", nullable: true),
                    OgImage = table.Column<string>(type: "text", nullable: true),
                    OgType = table.Column<string>(type: "text", nullable: true),
                    TwitterCard = table.Column<string>(type: "text", nullable: true),
                    TwitterTitle = table.Column<string>(type: "text", nullable: true),
                    TwitterDescription = table.Column<string>(type: "text", nullable: true),
                    TwitterImage = table.Column<string>(type: "text", nullable: true),
                    CanonicalUrl = table.Column<string>(type: "text", nullable: true),
                    Vendor = table.Column<string>(type: "text", nullable: true),
                    ProductType = table.Column<string>(type: "text", nullable: true),
                    Tags = table.Column<string>(type: "text", nullable: false),
                    Collections = table.Column<string>(type: "text", nullable: false),
                    PublishedScope = table.Column<string>(type: "text", nullable: false),
                    TemplateSuffix = table.Column<string>(type: "text", nullable: true),
                    IsGiftCard = table.Column<bool>(type: "boolean", nullable: false),
                    InventoryManagement = table.Column<string>(type: "text", nullable: true),
                    FulfillmentService = table.Column<string>(type: "text", nullable: true),
                    CountryOfOrigin = table.Column<string>(type: "text", nullable: true),
                    HSCode = table.Column<string>(type: "text", nullable: true),
                    MinQuantity = table.Column<int>(type: "integer", nullable: true),
                    MaxQuantity = table.Column<int>(type: "integer", nullable: true),
                    IncrementQuantity = table.Column<int>(type: "integer", nullable: true),
                    SalesChannels = table.Column<string>(type: "text", nullable: false),
                    VideoUrl = table.Column<string>(type: "text", nullable: true),
                    VideoThumbnailUrl = table.Column<string>(type: "text", nullable: true),
                    CustomFieldsJson = table.Column<string>(type: "text", nullable: true),
                    DefaultInventoryLocationId = table.Column<Guid>(type: "uuid", nullable: true),
                    BarcodeFormat = table.Column<string>(type: "text", nullable: true),
                    UnitPrice = table.Column<decimal>(type: "numeric", nullable: true),
                    UnitPriceUnit = table.Column<string>(type: "text", nullable: true),
                    ChargeTaxes = table.Column<bool>(type: "boolean", nullable: false),
                    TaxCategory = table.Column<string>(type: "text", nullable: true),
                    TaxRateId = table.Column<Guid>(type: "uuid", nullable: true),
                    FulfillmentStatus = table.Column<string>(type: "text", nullable: true),
                    RequiresShipping = table.Column<bool>(type: "boolean", nullable: false),
                    IsDigital = table.Column<bool>(type: "boolean", nullable: false),
                    ProductTagId = table.Column<Guid>(type: "uuid", nullable: true),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Products", x => x.Id);
                    table.ForeignKey(
                        name: "FK_Products_ProductTags_ProductTagId",
                        column: x => x.ProductTagId,
                        principalSchema: "products",
                        principalTable: "ProductTags",
                        principalColumn: "Id");
                    table.ForeignKey(
                        name: "FK_Products_TaxRates_TaxRateId",
                        column: x => x.TaxRateId,
                        principalSchema: "products",
                        principalTable: "TaxRates",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.SetNull);
                    table.ForeignKey(
                        name: "FK_Products_Tenants_TenantId",
                        column: x => x.TenantId,
                        principalSchema: "products",
                        principalTable: "Tenants",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "WarehouseLocation",
                schema: "products",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    TenantId = table.Column<Guid>(type: "uuid", nullable: false),
                    WarehouseId = table.Column<Guid>(type: "uuid", nullable: false),
                    Zone = table.Column<string>(type: "text", nullable: true),
                    Aisle = table.Column<string>(type: "text", nullable: true),
                    Rack = table.Column<string>(type: "text", nullable: true),
                    Shelf = table.Column<string>(type: "text", nullable: true),
                    Level = table.Column<string>(type: "text", nullable: true),
                    LocationCode = table.Column<string>(type: "text", nullable: false),
                    Name = table.Column<string>(type: "text", nullable: true),
                    Description = table.Column<string>(type: "text", nullable: true),
                    Width = table.Column<decimal>(type: "numeric", nullable: true),
                    Height = table.Column<decimal>(type: "numeric", nullable: true),
                    Depth = table.Column<decimal>(type: "numeric", nullable: true),
                    MaxWeight = table.Column<decimal>(type: "numeric", nullable: true),
                    IsActive = table.Column<bool>(type: "boolean", nullable: false),
                    IsReserved = table.Column<bool>(type: "boolean", nullable: false),
                    ReservedFor = table.Column<string>(type: "text", nullable: true),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_WarehouseLocation", x => x.Id);
                    table.ForeignKey(
                        name: "FK_WarehouseLocation_Tenants_TenantId",
                        column: x => x.TenantId,
                        principalSchema: "products",
                        principalTable: "Tenants",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_WarehouseLocation_Warehouses_WarehouseId",
                        column: x => x.WarehouseId,
                        principalSchema: "products",
                        principalTable: "Warehouses",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "WebhookDeliveries",
                schema: "products",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    WebhookId = table.Column<Guid>(type: "uuid", nullable: false),
                    Event = table.Column<string>(type: "text", nullable: false),
                    Payload = table.Column<string>(type: "text", nullable: false),
                    StatusCode = table.Column<int>(type: "integer", nullable: false),
                    ResponseBody = table.Column<string>(type: "text", nullable: true),
                    DeliveredAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    RetryCount = table.Column<int>(type: "integer", nullable: false),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_WebhookDeliveries", x => x.Id);
                    table.ForeignKey(
                        name: "FK_WebhookDeliveries_Webhooks_WebhookId",
                        column: x => x.WebhookId,
                        principalSchema: "products",
                        principalTable: "Webhooks",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "CouponExcludedProducts",
                schema: "products",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    CouponId = table.Column<Guid>(type: "uuid", nullable: false),
                    ProductId = table.Column<Guid>(type: "uuid", nullable: false),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_CouponExcludedProducts", x => x.Id);
                    table.ForeignKey(
                        name: "FK_CouponExcludedProducts_Coupons_CouponId",
                        column: x => x.CouponId,
                        principalSchema: "products",
                        principalTable: "Coupons",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_CouponExcludedProducts_Products_ProductId",
                        column: x => x.ProductId,
                        principalSchema: "products",
                        principalTable: "Products",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateTable(
                name: "CouponProducts",
                schema: "products",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    CouponId = table.Column<Guid>(type: "uuid", nullable: false),
                    ProductId = table.Column<Guid>(type: "uuid", nullable: false),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_CouponProducts", x => x.Id);
                    table.ForeignKey(
                        name: "FK_CouponProducts_Coupons_CouponId",
                        column: x => x.CouponId,
                        principalSchema: "products",
                        principalTable: "Coupons",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_CouponProducts_Products_ProductId",
                        column: x => x.ProductId,
                        principalSchema: "products",
                        principalTable: "Products",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateTable(
                name: "NavigationMenus",
                schema: "products",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    TenantId = table.Column<Guid>(type: "uuid", nullable: false),
                    Title = table.Column<string>(type: "text", nullable: false),
                    Url = table.Column<string>(type: "text", nullable: true),
                    ItemType = table.Column<int>(type: "integer", nullable: false),
                    PageId = table.Column<Guid>(type: "uuid", nullable: true),
                    CategoryId = table.Column<Guid>(type: "uuid", nullable: true),
                    ProductId = table.Column<Guid>(type: "uuid", nullable: true),
                    ParentId = table.Column<Guid>(type: "uuid", nullable: true),
                    Location = table.Column<int>(type: "integer", nullable: false),
                    SortOrder = table.Column<int>(type: "integer", nullable: false),
                    IsVisible = table.Column<bool>(type: "boolean", nullable: false),
                    OpenInNewTab = table.Column<bool>(type: "boolean", nullable: false),
                    Icon = table.Column<string>(type: "text", nullable: true),
                    CssClass = table.Column<string>(type: "text", nullable: true),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_NavigationMenus", x => x.Id);
                    table.ForeignKey(
                        name: "FK_NavigationMenus_Categories_CategoryId",
                        column: x => x.CategoryId,
                        principalSchema: "products",
                        principalTable: "Categories",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.SetNull);
                    table.ForeignKey(
                        name: "FK_NavigationMenus_NavigationMenus_ParentId",
                        column: x => x.ParentId,
                        principalSchema: "products",
                        principalTable: "NavigationMenus",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_NavigationMenus_Pages_PageId",
                        column: x => x.PageId,
                        principalSchema: "products",
                        principalTable: "Pages",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.SetNull);
                    table.ForeignKey(
                        name: "FK_NavigationMenus_Products_ProductId",
                        column: x => x.ProductId,
                        principalSchema: "products",
                        principalTable: "Products",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.SetNull);
                    table.ForeignKey(
                        name: "FK_NavigationMenus_Tenants_TenantId",
                        column: x => x.TenantId,
                        principalSchema: "products",
                        principalTable: "Tenants",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "ProductCategories",
                schema: "products",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    ProductId = table.Column<Guid>(type: "uuid", nullable: false),
                    CategoryId = table.Column<Guid>(type: "uuid", nullable: false),
                    IsPrimary = table.Column<bool>(type: "boolean", nullable: false),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_ProductCategories", x => x.Id);
                    table.ForeignKey(
                        name: "FK_ProductCategories_Categories_CategoryId",
                        column: x => x.CategoryId,
                        principalSchema: "products",
                        principalTable: "Categories",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_ProductCategories_Products_ProductId",
                        column: x => x.ProductId,
                        principalSchema: "products",
                        principalTable: "Products",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "ProductImages",
                schema: "products",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    ProductId = table.Column<Guid>(type: "uuid", nullable: false),
                    Position = table.Column<int>(type: "integer", nullable: false),
                    AltText = table.Column<string>(type: "text", nullable: false),
                    OriginalUrl = table.Column<string>(type: "text", nullable: false),
                    OriginalSizeBytes = table.Column<long>(type: "bigint", nullable: false),
                    OriginalWidth = table.Column<int>(type: "integer", nullable: false),
                    OriginalHeight = table.Column<int>(type: "integer", nullable: false),
                    ThumbnailUrl = table.Column<string>(type: "text", nullable: true),
                    SmallUrl = table.Column<string>(type: "text", nullable: true),
                    MediumUrl = table.Column<string>(type: "text", nullable: true),
                    LargeUrl = table.Column<string>(type: "text", nullable: true),
                    IsFeatured = table.Column<bool>(type: "boolean", nullable: false),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_ProductImages", x => x.Id);
                    table.ForeignKey(
                        name: "FK_ProductImages_Products_ProductId",
                        column: x => x.ProductId,
                        principalSchema: "products",
                        principalTable: "Products",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "ProductMetafields",
                schema: "products",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    ProductId = table.Column<Guid>(type: "uuid", nullable: false),
                    Namespace = table.Column<string>(type: "text", nullable: false),
                    Key = table.Column<string>(type: "text", nullable: false),
                    Value = table.Column<string>(type: "text", nullable: false),
                    Type = table.Column<string>(type: "text", nullable: false),
                    Description = table.Column<string>(type: "text", nullable: true),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_ProductMetafields", x => x.Id);
                    table.ForeignKey(
                        name: "FK_ProductMetafields_Products_ProductId",
                        column: x => x.ProductId,
                        principalSchema: "products",
                        principalTable: "Products",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "ProductOptions",
                schema: "products",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    ProductId = table.Column<Guid>(type: "uuid", nullable: false),
                    Name = table.Column<string>(type: "text", nullable: false),
                    Position = table.Column<int>(type: "integer", nullable: false),
                    Values = table.Column<string>(type: "text", nullable: false),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_ProductOptions", x => x.Id);
                    table.ForeignKey(
                        name: "FK_ProductOptions_Products_ProductId",
                        column: x => x.ProductId,
                        principalSchema: "products",
                        principalTable: "Products",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "ProductVariants",
                schema: "products",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    TenantId = table.Column<Guid>(type: "uuid", nullable: false),
                    ProductId = table.Column<Guid>(type: "uuid", nullable: false),
                    Title = table.Column<string>(type: "text", nullable: false),
                    SKU = table.Column<string>(type: "text", nullable: true),
                    Price = table.Column<decimal>(type: "numeric", nullable: false),
                    CompareAtPrice = table.Column<decimal>(type: "numeric", nullable: true),
                    CostPerItem = table.Column<decimal>(type: "numeric", nullable: false),
                    TrackInventory = table.Column<bool>(type: "boolean", nullable: false),
                    InventoryQuantity = table.Column<int>(type: "integer", nullable: true),
                    OptionValuesJson = table.Column<string>(type: "text", nullable: true),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_ProductVariants", x => x.Id);
                    table.ForeignKey(
                        name: "FK_ProductVariants_Products_ProductId",
                        column: x => x.ProductId,
                        principalSchema: "products",
                        principalTable: "Products",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "ResellerPrices",
                schema: "products",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    TenantId = table.Column<Guid>(type: "uuid", nullable: false),
                    ResellerId = table.Column<Guid>(type: "uuid", nullable: false),
                    ProductId = table.Column<Guid>(type: "uuid", nullable: false),
                    Price = table.Column<decimal>(type: "numeric", nullable: false),
                    CompareAtPrice = table.Column<decimal>(type: "numeric", nullable: true),
                    Currency = table.Column<string>(type: "text", nullable: false),
                    MinQuantity = table.Column<int>(type: "integer", nullable: true),
                    MaxQuantity = table.Column<int>(type: "integer", nullable: true),
                    IsActive = table.Column<bool>(type: "boolean", nullable: false),
                    ValidFrom = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    ValidUntil = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    Notes = table.Column<string>(type: "text", nullable: true),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_ResellerPrices", x => x.Id);
                    table.ForeignKey(
                        name: "FK_ResellerPrices_Products_ProductId",
                        column: x => x.ProductId,
                        principalSchema: "products",
                        principalTable: "Products",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_ResellerPrices_Resellers_ResellerId",
                        column: x => x.ResellerId,
                        principalSchema: "products",
                        principalTable: "Resellers",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_ResellerPrices_Tenants_TenantId",
                        column: x => x.TenantId,
                        principalSchema: "products",
                        principalTable: "Tenants",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "TaxRules",
                schema: "products",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    TenantId = table.Column<Guid>(type: "uuid", nullable: false),
                    Name = table.Column<string>(type: "text", nullable: false),
                    ProductId = table.Column<Guid>(type: "uuid", nullable: true),
                    CategoryId = table.Column<Guid>(type: "uuid", nullable: true),
                    ProductTypeId = table.Column<Guid>(type: "uuid", nullable: true),
                    TaxRateId = table.Column<Guid>(type: "uuid", nullable: false),
                    Priority = table.Column<int>(type: "integer", nullable: false),
                    IsActive = table.Column<bool>(type: "boolean", nullable: false),
                    MinPrice = table.Column<decimal>(type: "numeric", nullable: true),
                    MaxPrice = table.Column<decimal>(type: "numeric", nullable: true),
                    CountryCode = table.Column<string>(type: "text", nullable: true),
                    Region = table.Column<string>(type: "text", nullable: true),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_TaxRules", x => x.Id);
                    table.ForeignKey(
                        name: "FK_TaxRules_Categories_CategoryId",
                        column: x => x.CategoryId,
                        principalSchema: "products",
                        principalTable: "Categories",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.SetNull);
                    table.ForeignKey(
                        name: "FK_TaxRules_Products_ProductId",
                        column: x => x.ProductId,
                        principalSchema: "products",
                        principalTable: "Products",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.SetNull);
                    table.ForeignKey(
                        name: "FK_TaxRules_TaxRates_TaxRateId",
                        column: x => x.TaxRateId,
                        principalSchema: "products",
                        principalTable: "TaxRates",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_TaxRules_Tenants_TenantId",
                        column: x => x.TenantId,
                        principalSchema: "products",
                        principalTable: "Tenants",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "ProductInventories",
                schema: "products",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    TenantId = table.Column<Guid>(type: "uuid", nullable: false),
                    ProductId = table.Column<Guid>(type: "uuid", nullable: false),
                    WarehouseId = table.Column<Guid>(type: "uuid", nullable: false),
                    WarehouseLocationId = table.Column<Guid>(type: "uuid", nullable: true),
                    Location = table.Column<string>(type: "text", nullable: true),
                    Quantity = table.Column<int>(type: "integer", nullable: false),
                    ReservedQuantity = table.Column<int>(type: "integer", nullable: false),
                    MinStockLevel = table.Column<int>(type: "integer", nullable: true),
                    MaxStockLevel = table.Column<int>(type: "integer", nullable: true),
                    Cost = table.Column<decimal>(type: "numeric", nullable: true),
                    InventoryMethod = table.Column<string>(type: "text", nullable: true),
                    LotNumber = table.Column<string>(type: "text", nullable: true),
                    ExpiryDate = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    ManufactureDate = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    IsActive = table.Column<bool>(type: "boolean", nullable: false),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_ProductInventories", x => x.Id);
                    table.ForeignKey(
                        name: "FK_ProductInventories_Products_ProductId",
                        column: x => x.ProductId,
                        principalSchema: "products",
                        principalTable: "Products",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_ProductInventories_Tenants_TenantId",
                        column: x => x.TenantId,
                        principalSchema: "products",
                        principalTable: "Tenants",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_ProductInventories_WarehouseLocation_WarehouseLocationId",
                        column: x => x.WarehouseLocationId,
                        principalSchema: "products",
                        principalTable: "WarehouseLocation",
                        principalColumn: "Id");
                    table.ForeignKey(
                        name: "FK_ProductInventories_Warehouses_WarehouseId",
                        column: x => x.WarehouseId,
                        principalSchema: "products",
                        principalTable: "Warehouses",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateTable(
                name: "CartItems",
                schema: "products",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    CartId = table.Column<Guid>(type: "uuid", nullable: false),
                    ProductId = table.Column<Guid>(type: "uuid", nullable: false),
                    ProductVariantId = table.Column<Guid>(type: "uuid", nullable: true),
                    Title = table.Column<string>(type: "text", nullable: false),
                    SKU = table.Column<string>(type: "text", nullable: true),
                    Quantity = table.Column<int>(type: "integer", nullable: false),
                    UnitPrice = table.Column<decimal>(type: "numeric", nullable: false),
                    TotalPrice = table.Column<decimal>(type: "numeric", nullable: false),
                    Currency = table.Column<string>(type: "text", nullable: false),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_CartItems", x => x.Id);
                    table.ForeignKey(
                        name: "FK_CartItems_Carts_CartId",
                        column: x => x.CartId,
                        principalSchema: "products",
                        principalTable: "Carts",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_CartItems_ProductVariants_ProductVariantId",
                        column: x => x.ProductVariantId,
                        principalSchema: "products",
                        principalTable: "ProductVariants",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_CartItems_Products_ProductId",
                        column: x => x.ProductId,
                        principalSchema: "products",
                        principalTable: "Products",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateTable(
                name: "CouponUsages",
                schema: "products",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    TenantId = table.Column<Guid>(type: "uuid", nullable: false),
                    CouponId = table.Column<Guid>(type: "uuid", nullable: false),
                    CustomerId = table.Column<Guid>(type: "uuid", nullable: true),
                    OrderId = table.Column<Guid>(type: "uuid", nullable: false),
                    DiscountAmount = table.Column<decimal>(type: "numeric", nullable: false),
                    UsedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_CouponUsages", x => x.Id);
                    table.ForeignKey(
                        name: "FK_CouponUsages_Coupons_CouponId",
                        column: x => x.CouponId,
                        principalSchema: "products",
                        principalTable: "Coupons",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_CouponUsages_Customers_CustomerId",
                        column: x => x.CustomerId,
                        principalSchema: "products",
                        principalTable: "Customers",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.SetNull);
                    table.ForeignKey(
                        name: "FK_CouponUsages_Tenants_TenantId",
                        column: x => x.TenantId,
                        principalSchema: "products",
                        principalTable: "Tenants",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "InvoiceItems",
                schema: "products",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    InvoiceId = table.Column<Guid>(type: "uuid", nullable: false),
                    ProductId = table.Column<Guid>(type: "uuid", nullable: false),
                    ProductVariantId = table.Column<Guid>(type: "uuid", nullable: true),
                    ItemName = table.Column<string>(type: "text", nullable: false),
                    ItemDescription = table.Column<string>(type: "text", nullable: true),
                    ItemCode = table.Column<string>(type: "text", nullable: true),
                    ProductServiceCode = table.Column<string>(type: "text", nullable: true),
                    Quantity = table.Column<int>(type: "integer", nullable: false),
                    Unit = table.Column<string>(type: "text", nullable: false),
                    UnitPrice = table.Column<decimal>(type: "numeric", nullable: false),
                    LineTotal = table.Column<decimal>(type: "numeric", nullable: false),
                    TaxRateId = table.Column<Guid>(type: "uuid", nullable: true),
                    TaxRatePercent = table.Column<decimal>(type: "numeric", nullable: false),
                    TaxAmount = table.Column<decimal>(type: "numeric", nullable: false),
                    LineTotalWithTax = table.Column<decimal>(type: "numeric", nullable: false),
                    DiscountAmount = table.Column<decimal>(type: "numeric", nullable: false),
                    DiscountPercent = table.Column<decimal>(type: "numeric", nullable: false),
                    Position = table.Column<int>(type: "integer", nullable: false),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_InvoiceItems", x => x.Id);
                    table.ForeignKey(
                        name: "FK_InvoiceItems_ProductVariants_ProductVariantId",
                        column: x => x.ProductVariantId,
                        principalSchema: "products",
                        principalTable: "ProductVariants",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.SetNull);
                    table.ForeignKey(
                        name: "FK_InvoiceItems_Products_ProductId",
                        column: x => x.ProductId,
                        principalSchema: "products",
                        principalTable: "Products",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_InvoiceItems_TaxRates_TaxRateId",
                        column: x => x.TaxRateId,
                        principalSchema: "products",
                        principalTable: "TaxRates",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.SetNull);
                });

            migrationBuilder.CreateTable(
                name: "Invoices",
                schema: "products",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    TenantId = table.Column<Guid>(type: "uuid", nullable: false),
                    InvoiceNumber = table.Column<string>(type: "text", nullable: false),
                    InvoiceSerial = table.Column<string>(type: "text", nullable: false),
                    InvoiceDate = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    DeliveryDate = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    InvoiceType = table.Column<string>(type: "text", nullable: false),
                    ProfileId = table.Column<string>(type: "text", nullable: false),
                    Status = table.Column<string>(type: "text", nullable: false),
                    StatusMessage = table.Column<string>(type: "text", nullable: true),
                    OrderId = table.Column<Guid>(type: "uuid", nullable: false),
                    CustomerName = table.Column<string>(type: "text", nullable: false),
                    CustomerVKN = table.Column<string>(type: "text", nullable: true),
                    CustomerTCKN = table.Column<string>(type: "text", nullable: true),
                    CustomerTaxOffice = table.Column<string>(type: "text", nullable: true),
                    CustomerTaxNumber = table.Column<string>(type: "text", nullable: true),
                    CustomerEmail = table.Column<string>(type: "text", nullable: true),
                    CustomerPhone = table.Column<string>(type: "text", nullable: true),
                    CustomerAddressLine1 = table.Column<string>(type: "text", nullable: true),
                    CustomerAddressLine2 = table.Column<string>(type: "text", nullable: true),
                    CustomerCity = table.Column<string>(type: "text", nullable: true),
                    CustomerState = table.Column<string>(type: "text", nullable: true),
                    CustomerPostalCode = table.Column<string>(type: "text", nullable: true),
                    CustomerCountry = table.Column<string>(type: "text", nullable: true),
                    Subtotal = table.Column<decimal>(type: "numeric", nullable: false),
                    TaxAmount = table.Column<decimal>(type: "numeric", nullable: false),
                    DiscountAmount = table.Column<decimal>(type: "numeric", nullable: false),
                    ShippingAmount = table.Column<decimal>(type: "numeric", nullable: false),
                    Total = table.Column<decimal>(type: "numeric", nullable: false),
                    TaxDetailsJson = table.Column<string>(type: "text", nullable: false),
                    Currency = table.Column<string>(type: "text", nullable: false),
                    PaymentMethod = table.Column<string>(type: "text", nullable: true),
                    PaymentDueDate = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    GIBInvoiceId = table.Column<string>(type: "text", nullable: true),
                    GIBInvoiceNumber = table.Column<string>(type: "text", nullable: true),
                    GIBSentAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    GIBApprovedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    GIBApprovalStatus = table.Column<string>(type: "text", nullable: true),
                    UBLXML = table.Column<string>(type: "text", nullable: true),
                    UBLXMLSigned = table.Column<string>(type: "text", nullable: true),
                    PDFUrl = table.Column<string>(type: "text", nullable: true),
                    PDFGeneratedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    Notes = table.Column<string>(type: "text", nullable: true),
                    InternalNotes = table.Column<string>(type: "text", nullable: true),
                    IsCancelled = table.Column<bool>(type: "boolean", nullable: false),
                    CancelledAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    CancellationReason = table.Column<string>(type: "text", nullable: true),
                    CancellationInvoiceNumber = table.Column<string>(type: "text", nullable: true),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Invoices", x => x.Id);
                    table.ForeignKey(
                        name: "FK_Invoices_Tenants_TenantId",
                        column: x => x.TenantId,
                        principalSchema: "products",
                        principalTable: "Tenants",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "Orders",
                schema: "products",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    TenantId = table.Column<Guid>(type: "uuid", nullable: false),
                    OrderNumber = table.Column<string>(type: "text", nullable: false),
                    Status = table.Column<string>(type: "text", nullable: false),
                    CustomerEmail = table.Column<string>(type: "text", nullable: false),
                    CustomerPhone = table.Column<string>(type: "text", nullable: true),
                    CustomerFirstName = table.Column<string>(type: "text", nullable: true),
                    CustomerLastName = table.Column<string>(type: "text", nullable: true),
                    CustomerId = table.Column<Guid>(type: "uuid", nullable: true),
                    ShippingAddressLine1 = table.Column<string>(type: "text", nullable: true),
                    ShippingAddressLine2 = table.Column<string>(type: "text", nullable: true),
                    ShippingCity = table.Column<string>(type: "text", nullable: true),
                    ShippingState = table.Column<string>(type: "text", nullable: true),
                    ShippingPostalCode = table.Column<string>(type: "text", nullable: true),
                    ShippingCountry = table.Column<string>(type: "text", nullable: true),
                    TotalsJson = table.Column<string>(type: "text", nullable: false),
                    PaymentProvider = table.Column<string>(type: "text", nullable: true),
                    PaymentReference = table.Column<string>(type: "text", nullable: true),
                    PaymentStatus = table.Column<string>(type: "text", nullable: true),
                    PaidAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    ResellerId = table.Column<Guid>(type: "uuid", nullable: true),
                    IsResellerOrder = table.Column<bool>(type: "boolean", nullable: false),
                    CouponCode = table.Column<string>(type: "text", nullable: true),
                    CouponId = table.Column<Guid>(type: "uuid", nullable: true),
                    ShippingMethod = table.Column<string>(type: "text", nullable: true),
                    TrackingNumber = table.Column<string>(type: "text", nullable: true),
                    ShippedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    InvoiceId = table.Column<Guid>(type: "uuid", nullable: true),
                    InvoiceId1 = table.Column<Guid>(type: "uuid", nullable: true),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Orders", x => x.Id);
                    table.ForeignKey(
                        name: "FK_Orders_Coupons_CouponId",
                        column: x => x.CouponId,
                        principalSchema: "products",
                        principalTable: "Coupons",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.SetNull);
                    table.ForeignKey(
                        name: "FK_Orders_Customers_CustomerId",
                        column: x => x.CustomerId,
                        principalSchema: "products",
                        principalTable: "Customers",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.SetNull);
                    table.ForeignKey(
                        name: "FK_Orders_Invoices_InvoiceId1",
                        column: x => x.InvoiceId1,
                        principalSchema: "products",
                        principalTable: "Invoices",
                        principalColumn: "Id");
                    table.ForeignKey(
                        name: "FK_Orders_Resellers_ResellerId",
                        column: x => x.ResellerId,
                        principalSchema: "products",
                        principalTable: "Resellers",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.SetNull);
                    table.ForeignKey(
                        name: "FK_Orders_Tenants_TenantId",
                        column: x => x.TenantId,
                        principalSchema: "products",
                        principalTable: "Tenants",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "NotificationLogs",
                schema: "products",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    TenantId = table.Column<Guid>(type: "uuid", nullable: false),
                    Type = table.Column<int>(type: "integer", nullable: false),
                    Channel = table.Column<int>(type: "integer", nullable: false),
                    Recipient = table.Column<string>(type: "text", nullable: false),
                    RecipientName = table.Column<string>(type: "text", nullable: true),
                    CustomerId = table.Column<Guid>(type: "uuid", nullable: true),
                    Subject = table.Column<string>(type: "text", nullable: false),
                    Body = table.Column<string>(type: "text", nullable: false),
                    IsSent = table.Column<bool>(type: "boolean", nullable: false),
                    SentAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    IsDelivered = table.Column<bool>(type: "boolean", nullable: false),
                    DeliveredAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    IsFailed = table.Column<bool>(type: "boolean", nullable: false),
                    FailureReason = table.Column<string>(type: "text", nullable: true),
                    OrderId = table.Column<Guid>(type: "uuid", nullable: true),
                    ProductId = table.Column<Guid>(type: "uuid", nullable: true),
                    ProviderMessageId = table.Column<string>(type: "text", nullable: true),
                    Metadata = table.Column<string>(type: "text", nullable: true),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_NotificationLogs", x => x.Id);
                    table.ForeignKey(
                        name: "FK_NotificationLogs_Customers_CustomerId",
                        column: x => x.CustomerId,
                        principalSchema: "products",
                        principalTable: "Customers",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.SetNull);
                    table.ForeignKey(
                        name: "FK_NotificationLogs_Orders_OrderId",
                        column: x => x.OrderId,
                        principalSchema: "products",
                        principalTable: "Orders",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.SetNull);
                    table.ForeignKey(
                        name: "FK_NotificationLogs_Tenants_TenantId",
                        column: x => x.TenantId,
                        principalSchema: "products",
                        principalTable: "Tenants",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "OrderItems",
                schema: "products",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    OrderId = table.Column<Guid>(type: "uuid", nullable: false),
                    ProductId = table.Column<Guid>(type: "uuid", nullable: false),
                    ProductVariantId = table.Column<Guid>(type: "uuid", nullable: true),
                    Title = table.Column<string>(type: "text", nullable: false),
                    SKU = table.Column<string>(type: "text", nullable: true),
                    Quantity = table.Column<int>(type: "integer", nullable: false),
                    UnitPrice = table.Column<decimal>(type: "numeric", nullable: false),
                    TotalPrice = table.Column<decimal>(type: "numeric", nullable: false),
                    WarehouseId = table.Column<Guid>(type: "uuid", nullable: true),
                    WarehouseLocationId = table.Column<Guid>(type: "uuid", nullable: true),
                    IsPicked = table.Column<bool>(type: "boolean", nullable: false),
                    PickedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    PickedByUserId = table.Column<Guid>(type: "uuid", nullable: true),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_OrderItems", x => x.Id);
                    table.ForeignKey(
                        name: "FK_OrderItems_Orders_OrderId",
                        column: x => x.OrderId,
                        principalSchema: "products",
                        principalTable: "Orders",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_OrderItems_ProductVariants_ProductVariantId",
                        column: x => x.ProductVariantId,
                        principalSchema: "products",
                        principalTable: "ProductVariants",
                        principalColumn: "Id");
                    table.ForeignKey(
                        name: "FK_OrderItems_Products_ProductId",
                        column: x => x.ProductId,
                        principalSchema: "products",
                        principalTable: "Products",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_OrderItems_Users_PickedByUserId",
                        column: x => x.PickedByUserId,
                        principalSchema: "products",
                        principalTable: "Users",
                        principalColumn: "Id");
                    table.ForeignKey(
                        name: "FK_OrderItems_WarehouseLocation_WarehouseLocationId",
                        column: x => x.WarehouseLocationId,
                        principalSchema: "products",
                        principalTable: "WarehouseLocation",
                        principalColumn: "Id");
                    table.ForeignKey(
                        name: "FK_OrderItems_Warehouses_WarehouseId",
                        column: x => x.WarehouseId,
                        principalSchema: "products",
                        principalTable: "Warehouses",
                        principalColumn: "Id");
                });

            migrationBuilder.CreateTable(
                name: "ProductReviews",
                schema: "products",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    TenantId = table.Column<Guid>(type: "uuid", nullable: false),
                    ProductId = table.Column<Guid>(type: "uuid", nullable: false),
                    CustomerId = table.Column<Guid>(type: "uuid", nullable: true),
                    ReviewerName = table.Column<string>(type: "text", nullable: true),
                    ReviewerEmail = table.Column<string>(type: "text", nullable: true),
                    Rating = table.Column<int>(type: "integer", nullable: false),
                    Comment = table.Column<string>(type: "text", nullable: true),
                    Title = table.Column<string>(type: "text", nullable: true),
                    IsApproved = table.Column<bool>(type: "boolean", nullable: false),
                    IsPublished = table.Column<bool>(type: "boolean", nullable: false),
                    ModerationNote = table.Column<string>(type: "text", nullable: true),
                    ReplyText = table.Column<string>(type: "text", nullable: true),
                    RepliedBy = table.Column<Guid>(type: "uuid", nullable: true),
                    RepliedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    HelpfulCount = table.Column<int>(type: "integer", nullable: false),
                    NotHelpfulCount = table.Column<int>(type: "integer", nullable: false),
                    OrderId = table.Column<Guid>(type: "uuid", nullable: true),
                    IsVerifiedPurchase = table.Column<bool>(type: "boolean", nullable: false),
                    ImageUrls = table.Column<string>(type: "text", nullable: false),
                    ReviewType = table.Column<string>(type: "text", nullable: false),
                    ProductId1 = table.Column<Guid>(type: "uuid", nullable: true),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_ProductReviews", x => x.Id);
                    table.ForeignKey(
                        name: "FK_ProductReviews_Customers_CustomerId",
                        column: x => x.CustomerId,
                        principalSchema: "products",
                        principalTable: "Customers",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.SetNull);
                    table.ForeignKey(
                        name: "FK_ProductReviews_Orders_OrderId",
                        column: x => x.OrderId,
                        principalSchema: "products",
                        principalTable: "Orders",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.SetNull);
                    table.ForeignKey(
                        name: "FK_ProductReviews_Products_ProductId",
                        column: x => x.ProductId,
                        principalSchema: "products",
                        principalTable: "Products",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_ProductReviews_Products_ProductId1",
                        column: x => x.ProductId1,
                        principalSchema: "products",
                        principalTable: "Products",
                        principalColumn: "Id");
                    table.ForeignKey(
                        name: "FK_ProductReviews_Tenants_TenantId",
                        column: x => x.TenantId,
                        principalSchema: "products",
                        principalTable: "Tenants",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "Shipments",
                schema: "products",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    TenantId = table.Column<Guid>(type: "uuid", nullable: false),
                    OrderId = table.Column<Guid>(type: "uuid", nullable: false),
                    ShippingProviderId = table.Column<Guid>(type: "uuid", nullable: false),
                    TrackingNumber = table.Column<string>(type: "text", nullable: false),
                    LabelUrl = table.Column<string>(type: "text", nullable: true),
                    Status = table.Column<string>(type: "text", nullable: false),
                    Weight = table.Column<decimal>(type: "numeric", nullable: false),
                    Width = table.Column<decimal>(type: "numeric", nullable: true),
                    Height = table.Column<decimal>(type: "numeric", nullable: true),
                    Depth = table.Column<decimal>(type: "numeric", nullable: true),
                    PackageCount = table.Column<int>(type: "integer", nullable: false),
                    ShippingCost = table.Column<decimal>(type: "numeric", nullable: false),
                    Currency = table.Column<string>(type: "text", nullable: false),
                    ShippedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    DeliveredAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    EstimatedDeliveryDate = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    RecipientName = table.Column<string>(type: "text", nullable: false),
                    RecipientPhone = table.Column<string>(type: "text", nullable: false),
                    AddressLine1 = table.Column<string>(type: "text", nullable: false),
                    AddressLine2 = table.Column<string>(type: "text", nullable: true),
                    City = table.Column<string>(type: "text", nullable: false),
                    State = table.Column<string>(type: "text", nullable: false),
                    PostalCode = table.Column<string>(type: "text", nullable: false),
                    Country = table.Column<string>(type: "text", nullable: false),
                    ProviderResponseJson = table.Column<string>(type: "text", nullable: true),
                    ErrorMessage = table.Column<string>(type: "text", nullable: true),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Shipments", x => x.Id);
                    table.ForeignKey(
                        name: "FK_Shipments_Orders_OrderId",
                        column: x => x.OrderId,
                        principalSchema: "products",
                        principalTable: "Orders",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_Shipments_ShippingProviders_ShippingProviderId",
                        column: x => x.ShippingProviderId,
                        principalSchema: "products",
                        principalTable: "ShippingProviders",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_Shipments_Tenants_TenantId",
                        column: x => x.TenantId,
                        principalSchema: "products",
                        principalTable: "Tenants",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "ReviewVotes",
                schema: "products",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    TenantId = table.Column<Guid>(type: "uuid", nullable: false),
                    ReviewId = table.Column<Guid>(type: "uuid", nullable: false),
                    CustomerId = table.Column<Guid>(type: "uuid", nullable: true),
                    IpAddress = table.Column<string>(type: "text", nullable: true),
                    IsHelpful = table.Column<bool>(type: "boolean", nullable: false),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_ReviewVotes", x => x.Id);
                    table.ForeignKey(
                        name: "FK_ReviewVotes_Customers_CustomerId",
                        column: x => x.CustomerId,
                        principalSchema: "products",
                        principalTable: "Customers",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.SetNull);
                    table.ForeignKey(
                        name: "FK_ReviewVotes_ProductReviews_ReviewId",
                        column: x => x.ReviewId,
                        principalSchema: "products",
                        principalTable: "ProductReviews",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_ReviewVotes_Tenants_TenantId",
                        column: x => x.TenantId,
                        principalSchema: "products",
                        principalTable: "Tenants",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateIndex(
                name: "IX_ApiKeys_TenantId",
                schema: "products",
                table: "ApiKeys",
                column: "TenantId");

            migrationBuilder.CreateIndex(
                name: "IX_AuditLogs_TenantId",
                schema: "products",
                table: "AuditLogs",
                column: "TenantId");

            migrationBuilder.CreateIndex(
                name: "IX_AuditLogs_UserId",
                schema: "products",
                table: "AuditLogs",
                column: "UserId");

            migrationBuilder.CreateIndex(
                name: "IX_CartItem_CartId_ProductId_ProductVariantId",
                schema: "products",
                table: "CartItems",
                columns: new[] { "CartId", "ProductId", "ProductVariantId" },
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_CartItems_ProductId",
                schema: "products",
                table: "CartItems",
                column: "ProductId");

            migrationBuilder.CreateIndex(
                name: "IX_CartItems_ProductVariantId",
                schema: "products",
                table: "CartItems",
                column: "ProductVariantId");

            migrationBuilder.CreateIndex(
                name: "IX_Cart_TenantId_CustomerId",
                schema: "products",
                table: "Carts",
                columns: new[] { "TenantId", "CustomerId" },
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_Carts_CouponId",
                schema: "products",
                table: "Carts",
                column: "CouponId");

            migrationBuilder.CreateIndex(
                name: "IX_Carts_CustomerId",
                schema: "products",
                table: "Carts",
                column: "CustomerId");

            migrationBuilder.CreateIndex(
                name: "IX_Carts_TenantId",
                schema: "products",
                table: "Carts",
                column: "TenantId");

            migrationBuilder.CreateIndex(
                name: "IX_Categories_ParentCategoryId",
                schema: "products",
                table: "Categories",
                column: "ParentCategoryId");

            migrationBuilder.CreateIndex(
                name: "IX_Categories_TenantId",
                schema: "products",
                table: "Categories",
                column: "TenantId");

            migrationBuilder.CreateIndex(
                name: "IX_Category_TenantId_IsActive_ParentCategoryId",
                schema: "products",
                table: "Categories",
                columns: new[] { "TenantId", "IsActive", "ParentCategoryId" });

            migrationBuilder.CreateIndex(
                name: "IX_CouponCategories_CategoryId",
                schema: "products",
                table: "CouponCategories",
                column: "CategoryId");

            migrationBuilder.CreateIndex(
                name: "IX_CouponCategories_CouponId",
                schema: "products",
                table: "CouponCategories",
                column: "CouponId");

            migrationBuilder.CreateIndex(
                name: "IX_CouponCustomers_CouponId",
                schema: "products",
                table: "CouponCustomers",
                column: "CouponId");

            migrationBuilder.CreateIndex(
                name: "IX_CouponCustomers_CustomerId",
                schema: "products",
                table: "CouponCustomers",
                column: "CustomerId");

            migrationBuilder.CreateIndex(
                name: "IX_CouponExcludedProducts_CouponId",
                schema: "products",
                table: "CouponExcludedProducts",
                column: "CouponId");

            migrationBuilder.CreateIndex(
                name: "IX_CouponExcludedProducts_ProductId",
                schema: "products",
                table: "CouponExcludedProducts",
                column: "ProductId");

            migrationBuilder.CreateIndex(
                name: "IX_CouponProducts_CouponId",
                schema: "products",
                table: "CouponProducts",
                column: "CouponId");

            migrationBuilder.CreateIndex(
                name: "IX_CouponProducts_ProductId",
                schema: "products",
                table: "CouponProducts",
                column: "ProductId");

            migrationBuilder.CreateIndex(
                name: "IX_Coupon_TenantId_Code",
                schema: "products",
                table: "Coupons",
                columns: new[] { "TenantId", "Code" },
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_Coupon_TenantId_IsActive_ValidFrom_ValidTo",
                schema: "products",
                table: "Coupons",
                columns: new[] { "TenantId", "IsActive", "ValidFrom", "ValidTo" });

            migrationBuilder.CreateIndex(
                name: "IX_Coupons_TenantId",
                schema: "products",
                table: "Coupons",
                column: "TenantId");

            migrationBuilder.CreateIndex(
                name: "IX_CouponUsage_CouponId_CustomerId",
                schema: "products",
                table: "CouponUsages",
                columns: new[] { "CouponId", "CustomerId" });

            migrationBuilder.CreateIndex(
                name: "IX_CouponUsage_TenantId_UsedAt",
                schema: "products",
                table: "CouponUsages",
                columns: new[] { "TenantId", "UsedAt" });

            migrationBuilder.CreateIndex(
                name: "IX_CouponUsages_CustomerId",
                schema: "products",
                table: "CouponUsages",
                column: "CustomerId");

            migrationBuilder.CreateIndex(
                name: "IX_CouponUsages_OrderId",
                schema: "products",
                table: "CouponUsages",
                column: "OrderId");

            migrationBuilder.CreateIndex(
                name: "IX_CouponUsages_TenantId",
                schema: "products",
                table: "CouponUsages",
                column: "TenantId");

            migrationBuilder.CreateIndex(
                name: "IX_CustomerAddress_CustomerId_IsDefaultBilling",
                schema: "products",
                table: "CustomerAddresses",
                columns: new[] { "CustomerId", "IsDefaultBilling" });

            migrationBuilder.CreateIndex(
                name: "IX_CustomerAddress_CustomerId_IsDefaultShipping",
                schema: "products",
                table: "CustomerAddresses",
                columns: new[] { "CustomerId", "IsDefaultShipping" });

            migrationBuilder.CreateIndex(
                name: "IX_CustomerAddresses_TenantId",
                schema: "products",
                table: "CustomerAddresses",
                column: "TenantId");

            migrationBuilder.CreateIndex(
                name: "IX_Customer_TenantId_Email",
                schema: "products",
                table: "Customers",
                columns: new[] { "TenantId", "Email" },
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_Customer_TenantId_IsActive",
                schema: "products",
                table: "Customers",
                columns: new[] { "TenantId", "IsActive" });

            migrationBuilder.CreateIndex(
                name: "IX_Customers_TenantId",
                schema: "products",
                table: "Customers",
                column: "TenantId");

            migrationBuilder.CreateIndex(
                name: "IX_Domains_Host",
                schema: "products",
                table: "Domains",
                column: "Host",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_Domains_TenantId",
                schema: "products",
                table: "Domains",
                column: "TenantId");

            migrationBuilder.CreateIndex(
                name: "IX_EmailNotification_ReferenceType_ReferenceId",
                schema: "products",
                table: "EmailNotifications",
                columns: new[] { "ReferenceType", "ReferenceId" });

            migrationBuilder.CreateIndex(
                name: "IX_EmailNotification_TenantId_Status_CreatedAt",
                schema: "products",
                table: "EmailNotifications",
                columns: new[] { "TenantId", "Status", "CreatedAt" });

            migrationBuilder.CreateIndex(
                name: "IX_EmailNotification_TenantId_ToEmail_CreatedAt",
                schema: "products",
                table: "EmailNotifications",
                columns: new[] { "TenantId", "ToEmail", "CreatedAt" });

            migrationBuilder.CreateIndex(
                name: "IX_EmailNotifications_EmailProviderId",
                schema: "products",
                table: "EmailNotifications",
                column: "EmailProviderId");

            migrationBuilder.CreateIndex(
                name: "IX_EmailNotifications_EmailTemplateId",
                schema: "products",
                table: "EmailNotifications",
                column: "EmailTemplateId");

            migrationBuilder.CreateIndex(
                name: "IX_EmailNotifications_TenantId",
                schema: "products",
                table: "EmailNotifications",
                column: "TenantId");

            migrationBuilder.CreateIndex(
                name: "IX_EmailProvider_TenantId_IsActive_IsDefault",
                schema: "products",
                table: "EmailProviders",
                columns: new[] { "TenantId", "IsActive", "IsDefault" });

            migrationBuilder.CreateIndex(
                name: "IX_EmailProviders_TenantId",
                schema: "products",
                table: "EmailProviders",
                column: "TenantId");

            migrationBuilder.CreateIndex(
                name: "IX_EmailTemplate_TenantId_TemplateCode",
                schema: "products",
                table: "EmailTemplates",
                columns: new[] { "TenantId", "TemplateCode" },
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_EmailTemplates_TenantId",
                schema: "products",
                table: "EmailTemplates",
                column: "TenantId");

            migrationBuilder.CreateIndex(
                name: "IX_InvoiceItems_InvoiceId",
                schema: "products",
                table: "InvoiceItems",
                column: "InvoiceId");

            migrationBuilder.CreateIndex(
                name: "IX_InvoiceItems_ProductId",
                schema: "products",
                table: "InvoiceItems",
                column: "ProductId");

            migrationBuilder.CreateIndex(
                name: "IX_InvoiceItems_ProductVariantId",
                schema: "products",
                table: "InvoiceItems",
                column: "ProductVariantId");

            migrationBuilder.CreateIndex(
                name: "IX_InvoiceItems_TaxRateId",
                schema: "products",
                table: "InvoiceItems",
                column: "TaxRateId");

            migrationBuilder.CreateIndex(
                name: "IX_Invoice_TenantId_GIBInvoiceId",
                schema: "products",
                table: "Invoices",
                columns: new[] { "TenantId", "GIBInvoiceId" },
                filter: "\"GIBInvoiceId\" IS NOT NULL");

            migrationBuilder.CreateIndex(
                name: "IX_Invoice_TenantId_InvoiceNumber_InvoiceSerial",
                schema: "products",
                table: "Invoices",
                columns: new[] { "TenantId", "InvoiceNumber", "InvoiceSerial" },
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_Invoice_TenantId_OrderId",
                schema: "products",
                table: "Invoices",
                columns: new[] { "TenantId", "OrderId" });

            migrationBuilder.CreateIndex(
                name: "IX_Invoice_TenantId_Status_InvoiceDate",
                schema: "products",
                table: "Invoices",
                columns: new[] { "TenantId", "Status", "InvoiceDate" });

            migrationBuilder.CreateIndex(
                name: "IX_Invoices_OrderId",
                schema: "products",
                table: "Invoices",
                column: "OrderId");

            migrationBuilder.CreateIndex(
                name: "IX_Invoices_TenantId",
                schema: "products",
                table: "Invoices",
                column: "TenantId");

            migrationBuilder.CreateIndex(
                name: "IX_MarketplaceIntegrations_TenantId",
                schema: "products",
                table: "MarketplaceIntegrations",
                column: "TenantId");

            migrationBuilder.CreateIndex(
                name: "IX_NavigationMenu_TenantId_Location_SortOrder",
                schema: "products",
                table: "NavigationMenus",
                columns: new[] { "TenantId", "Location", "SortOrder" });

            migrationBuilder.CreateIndex(
                name: "IX_NavigationMenu_TenantId_ParentId_SortOrder",
                schema: "products",
                table: "NavigationMenus",
                columns: new[] { "TenantId", "ParentId", "SortOrder" });

            migrationBuilder.CreateIndex(
                name: "IX_NavigationMenus_CategoryId",
                schema: "products",
                table: "NavigationMenus",
                column: "CategoryId");

            migrationBuilder.CreateIndex(
                name: "IX_NavigationMenus_PageId",
                schema: "products",
                table: "NavigationMenus",
                column: "PageId");

            migrationBuilder.CreateIndex(
                name: "IX_NavigationMenus_ParentId",
                schema: "products",
                table: "NavigationMenus",
                column: "ParentId");

            migrationBuilder.CreateIndex(
                name: "IX_NavigationMenus_ProductId",
                schema: "products",
                table: "NavigationMenus",
                column: "ProductId");

            migrationBuilder.CreateIndex(
                name: "IX_NavigationMenus_TenantId",
                schema: "products",
                table: "NavigationMenus",
                column: "TenantId");

            migrationBuilder.CreateIndex(
                name: "IX_NotificationLog_TenantId_IsSent_IsFailed",
                schema: "products",
                table: "NotificationLogs",
                columns: new[] { "TenantId", "IsSent", "IsFailed" });

            migrationBuilder.CreateIndex(
                name: "IX_NotificationLog_TenantId_Recipient_CreatedAt",
                schema: "products",
                table: "NotificationLogs",
                columns: new[] { "TenantId", "Recipient", "CreatedAt" });

            migrationBuilder.CreateIndex(
                name: "IX_NotificationLog_TenantId_Type_CreatedAt",
                schema: "products",
                table: "NotificationLogs",
                columns: new[] { "TenantId", "Type", "CreatedAt" });

            migrationBuilder.CreateIndex(
                name: "IX_NotificationLogs_CustomerId",
                schema: "products",
                table: "NotificationLogs",
                column: "CustomerId");

            migrationBuilder.CreateIndex(
                name: "IX_NotificationLogs_OrderId",
                schema: "products",
                table: "NotificationLogs",
                column: "OrderId");

            migrationBuilder.CreateIndex(
                name: "IX_NotificationLogs_TenantId",
                schema: "products",
                table: "NotificationLogs",
                column: "TenantId");

            migrationBuilder.CreateIndex(
                name: "IX_OrderItems_OrderId",
                schema: "products",
                table: "OrderItems",
                column: "OrderId");

            migrationBuilder.CreateIndex(
                name: "IX_OrderItems_PickedByUserId",
                schema: "products",
                table: "OrderItems",
                column: "PickedByUserId");

            migrationBuilder.CreateIndex(
                name: "IX_OrderItems_ProductId",
                schema: "products",
                table: "OrderItems",
                column: "ProductId");

            migrationBuilder.CreateIndex(
                name: "IX_OrderItems_ProductVariantId",
                schema: "products",
                table: "OrderItems",
                column: "ProductVariantId");

            migrationBuilder.CreateIndex(
                name: "IX_OrderItems_WarehouseId",
                schema: "products",
                table: "OrderItems",
                column: "WarehouseId");

            migrationBuilder.CreateIndex(
                name: "IX_OrderItems_WarehouseLocationId",
                schema: "products",
                table: "OrderItems",
                column: "WarehouseLocationId");

            migrationBuilder.CreateIndex(
                name: "IX_Order_TenantId_Status_CreatedAt",
                schema: "products",
                table: "Orders",
                columns: new[] { "TenantId", "Status", "CreatedAt" });

            migrationBuilder.CreateIndex(
                name: "IX_Orders_CouponId",
                schema: "products",
                table: "Orders",
                column: "CouponId");

            migrationBuilder.CreateIndex(
                name: "IX_Orders_CustomerId",
                schema: "products",
                table: "Orders",
                column: "CustomerId");

            migrationBuilder.CreateIndex(
                name: "IX_Orders_InvoiceId1",
                schema: "products",
                table: "Orders",
                column: "InvoiceId1");

            migrationBuilder.CreateIndex(
                name: "IX_Orders_ResellerId",
                schema: "products",
                table: "Orders",
                column: "ResellerId");

            migrationBuilder.CreateIndex(
                name: "IX_Orders_TenantId",
                schema: "products",
                table: "Orders",
                column: "TenantId");

            migrationBuilder.CreateIndex(
                name: "IX_Orders_TenantId_OrderNumber",
                schema: "products",
                table: "Orders",
                columns: new[] { "TenantId", "OrderNumber" },
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_Page_TenantId_IsPublished_SortOrder",
                schema: "products",
                table: "Pages",
                columns: new[] { "TenantId", "IsPublished", "SortOrder" });

            migrationBuilder.CreateIndex(
                name: "IX_Page_TenantId_Slug",
                schema: "products",
                table: "Pages",
                columns: new[] { "TenantId", "Slug" },
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_Page_TenantId_SystemPageType",
                schema: "products",
                table: "Pages",
                columns: new[] { "TenantId", "SystemPageType" },
                filter: "\"SystemPageType\" IS NOT NULL");

            migrationBuilder.CreateIndex(
                name: "IX_Pages_TenantId",
                schema: "products",
                table: "Pages",
                column: "TenantId");

            migrationBuilder.CreateIndex(
                name: "IX_PaymentProvider_TenantId_IsActive_IsDefault",
                schema: "products",
                table: "PaymentProviders",
                columns: new[] { "TenantId", "IsActive", "IsDefault" });

            migrationBuilder.CreateIndex(
                name: "IX_PaymentProvider_TenantId_ProviderCode",
                schema: "products",
                table: "PaymentProviders",
                columns: new[] { "TenantId", "ProviderCode" },
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_PaymentProviders_TenantId",
                schema: "products",
                table: "PaymentProviders",
                column: "TenantId");

            migrationBuilder.CreateIndex(
                name: "IX_ProductCategories_ProductId",
                schema: "products",
                table: "ProductCategories",
                column: "ProductId");

            migrationBuilder.CreateIndex(
                name: "IX_ProductCategory_CategoryId_ProductId",
                schema: "products",
                table: "ProductCategories",
                columns: new[] { "CategoryId", "ProductId" },
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_ProductImages_ProductId_Position",
                schema: "products",
                table: "ProductImages",
                columns: new[] { "ProductId", "Position" });

            migrationBuilder.CreateIndex(
                name: "IX_ProductInventories_ProductId_WarehouseId",
                schema: "products",
                table: "ProductInventories",
                columns: new[] { "ProductId", "WarehouseId" },
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_ProductInventories_TenantId",
                schema: "products",
                table: "ProductInventories",
                column: "TenantId");

            migrationBuilder.CreateIndex(
                name: "IX_ProductInventories_WarehouseId",
                schema: "products",
                table: "ProductInventories",
                column: "WarehouseId");

            migrationBuilder.CreateIndex(
                name: "IX_ProductInventories_WarehouseLocationId",
                schema: "products",
                table: "ProductInventories",
                column: "WarehouseLocationId");

            migrationBuilder.CreateIndex(
                name: "IX_ProductMetafields_ProductId_Namespace_Key",
                schema: "products",
                table: "ProductMetafields",
                columns: new[] { "ProductId", "Namespace", "Key" },
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_ProductOptions_ProductId_Position",
                schema: "products",
                table: "ProductOptions",
                columns: new[] { "ProductId", "Position" });

            migrationBuilder.CreateIndex(
                name: "IX_ProductReview_TenantId_CustomerId",
                schema: "products",
                table: "ProductReviews",
                columns: new[] { "TenantId", "CustomerId" });

            migrationBuilder.CreateIndex(
                name: "IX_ProductReview_TenantId_IsApproved_IsPublished_CreatedAt",
                schema: "products",
                table: "ProductReviews",
                columns: new[] { "TenantId", "IsApproved", "IsPublished", "CreatedAt" });

            migrationBuilder.CreateIndex(
                name: "IX_ProductReview_TenantId_ProductId_IsPublished",
                schema: "products",
                table: "ProductReviews",
                columns: new[] { "TenantId", "ProductId", "IsPublished" });

            migrationBuilder.CreateIndex(
                name: "IX_ProductReview_TenantId_ProductId_Rating",
                schema: "products",
                table: "ProductReviews",
                columns: new[] { "TenantId", "ProductId", "Rating" });

            migrationBuilder.CreateIndex(
                name: "IX_ProductReviews_CustomerId",
                schema: "products",
                table: "ProductReviews",
                column: "CustomerId");

            migrationBuilder.CreateIndex(
                name: "IX_ProductReviews_OrderId",
                schema: "products",
                table: "ProductReviews",
                column: "OrderId");

            migrationBuilder.CreateIndex(
                name: "IX_ProductReviews_ProductId",
                schema: "products",
                table: "ProductReviews",
                column: "ProductId");

            migrationBuilder.CreateIndex(
                name: "IX_ProductReviews_ProductId1",
                schema: "products",
                table: "ProductReviews",
                column: "ProductId1");

            migrationBuilder.CreateIndex(
                name: "IX_ProductReviews_TenantId",
                schema: "products",
                table: "ProductReviews",
                column: "TenantId");

            migrationBuilder.CreateIndex(
                name: "IX_Product_TenantId_IsActive_CreatedAt",
                schema: "products",
                table: "Products",
                columns: new[] { "TenantId", "IsActive", "CreatedAt" });

            migrationBuilder.CreateIndex(
                name: "IX_Product_TenantId_Price",
                schema: "products",
                table: "Products",
                columns: new[] { "TenantId", "Price" });

            migrationBuilder.CreateIndex(
                name: "IX_Product_TenantId_SKU",
                schema: "products",
                table: "Products",
                columns: new[] { "TenantId", "SKU" },
                filter: "\"SKU\" IS NOT NULL");

            migrationBuilder.CreateIndex(
                name: "IX_Product_TenantId_Title",
                schema: "products",
                table: "Products",
                columns: new[] { "TenantId", "Title" });

            migrationBuilder.CreateIndex(
                name: "IX_Products_ProductTagId",
                schema: "products",
                table: "Products",
                column: "ProductTagId");

            migrationBuilder.CreateIndex(
                name: "IX_Products_TaxRateId",
                schema: "products",
                table: "Products",
                column: "TaxRateId");

            migrationBuilder.CreateIndex(
                name: "IX_Products_TenantId",
                schema: "products",
                table: "Products",
                column: "TenantId");

            migrationBuilder.CreateIndex(
                name: "IX_Products_TenantId_Slug",
                schema: "products",
                table: "Products",
                columns: new[] { "TenantId", "Slug" },
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_ProductTags_TenantId",
                schema: "products",
                table: "ProductTags",
                column: "TenantId");

            migrationBuilder.CreateIndex(
                name: "IX_ProductVariants_ProductId",
                schema: "products",
                table: "ProductVariants",
                column: "ProductId");

            migrationBuilder.CreateIndex(
                name: "IX_ProductVariants_TenantId",
                schema: "products",
                table: "ProductVariants",
                column: "TenantId");

            migrationBuilder.CreateIndex(
                name: "IX_ResellerPrice_ResellerId_ProductId_MinQuantity",
                schema: "products",
                table: "ResellerPrices",
                columns: new[] { "ResellerId", "ProductId", "MinQuantity" },
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_ResellerPrice_TenantId_ProductId_IsActive",
                schema: "products",
                table: "ResellerPrices",
                columns: new[] { "TenantId", "ProductId", "IsActive" });

            migrationBuilder.CreateIndex(
                name: "IX_ResellerPrices_ProductId",
                schema: "products",
                table: "ResellerPrices",
                column: "ProductId");

            migrationBuilder.CreateIndex(
                name: "IX_ResellerPrices_TenantId",
                schema: "products",
                table: "ResellerPrices",
                column: "TenantId");

            migrationBuilder.CreateIndex(
                name: "IX_Reseller_TenantId_Email",
                schema: "products",
                table: "Resellers",
                columns: new[] { "TenantId", "Email" },
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_Reseller_TenantId_IsActive",
                schema: "products",
                table: "Resellers",
                columns: new[] { "TenantId", "IsActive" });

            migrationBuilder.CreateIndex(
                name: "IX_Resellers_TenantId",
                schema: "products",
                table: "Resellers",
                column: "TenantId");

            migrationBuilder.CreateIndex(
                name: "IX_ReviewVote_TenantId_ReviewId_CustomerId",
                schema: "products",
                table: "ReviewVotes",
                columns: new[] { "TenantId", "ReviewId", "CustomerId" },
                filter: "\"CustomerId\" IS NOT NULL");

            migrationBuilder.CreateIndex(
                name: "IX_ReviewVote_TenantId_ReviewId_IpAddress",
                schema: "products",
                table: "ReviewVotes",
                columns: new[] { "TenantId", "ReviewId", "IpAddress" },
                filter: "\"IpAddress\" IS NOT NULL");

            migrationBuilder.CreateIndex(
                name: "IX_ReviewVotes_CustomerId",
                schema: "products",
                table: "ReviewVotes",
                column: "CustomerId");

            migrationBuilder.CreateIndex(
                name: "IX_ReviewVotes_ReviewId",
                schema: "products",
                table: "ReviewVotes",
                column: "ReviewId");

            migrationBuilder.CreateIndex(
                name: "IX_Shipment_TenantId_OrderId",
                schema: "products",
                table: "Shipments",
                columns: new[] { "TenantId", "OrderId" });

            migrationBuilder.CreateIndex(
                name: "IX_Shipment_TenantId_Status_ShippedAt",
                schema: "products",
                table: "Shipments",
                columns: new[] { "TenantId", "Status", "ShippedAt" });

            migrationBuilder.CreateIndex(
                name: "IX_Shipment_TenantId_TrackingNumber",
                schema: "products",
                table: "Shipments",
                columns: new[] { "TenantId", "TrackingNumber" },
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_Shipments_OrderId",
                schema: "products",
                table: "Shipments",
                column: "OrderId");

            migrationBuilder.CreateIndex(
                name: "IX_Shipments_ShippingProviderId",
                schema: "products",
                table: "Shipments",
                column: "ShippingProviderId");

            migrationBuilder.CreateIndex(
                name: "IX_Shipments_TenantId",
                schema: "products",
                table: "Shipments",
                column: "TenantId");

            migrationBuilder.CreateIndex(
                name: "IX_ShippingProvider_TenantId_IsActive_IsDefault",
                schema: "products",
                table: "ShippingProviders",
                columns: new[] { "TenantId", "IsActive", "IsDefault" });

            migrationBuilder.CreateIndex(
                name: "IX_ShippingProvider_TenantId_ProviderCode",
                schema: "products",
                table: "ShippingProviders",
                columns: new[] { "TenantId", "ProviderCode" },
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_ShippingProviders_TenantId",
                schema: "products",
                table: "ShippingProviders",
                column: "TenantId");

            migrationBuilder.CreateIndex(
                name: "IX_TaxRates_TenantId",
                schema: "products",
                table: "TaxRates",
                column: "TenantId");

            migrationBuilder.CreateIndex(
                name: "IX_TaxRates_TenantId_Code",
                schema: "products",
                table: "TaxRates",
                columns: new[] { "TenantId", "Code" },
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_TaxRules_CategoryId",
                schema: "products",
                table: "TaxRules",
                column: "CategoryId");

            migrationBuilder.CreateIndex(
                name: "IX_TaxRules_ProductId",
                schema: "products",
                table: "TaxRules",
                column: "ProductId");

            migrationBuilder.CreateIndex(
                name: "IX_TaxRules_TaxRateId",
                schema: "products",
                table: "TaxRules",
                column: "TaxRateId");

            migrationBuilder.CreateIndex(
                name: "IX_TaxRules_TenantId",
                schema: "products",
                table: "TaxRules",
                column: "TenantId");

            migrationBuilder.CreateIndex(
                name: "IX_Template_Code_IsActive",
                schema: "products",
                table: "Templates",
                columns: new[] { "Code", "IsActive" });

            migrationBuilder.CreateIndex(
                name: "IX_Templates_Code_Version",
                schema: "products",
                table: "Templates",
                columns: new[] { "Code", "Version" },
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_TenantInvoiceSettings_TenantId",
                schema: "products",
                table: "TenantInvoiceSettings",
                column: "TenantId",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_Tenants_PlanId",
                schema: "products",
                table: "Tenants",
                column: "PlanId");

            migrationBuilder.CreateIndex(
                name: "IX_Tenants_TemplateId",
                schema: "products",
                table: "Tenants",
                column: "TemplateId");

            migrationBuilder.CreateIndex(
                name: "IX_UserTenantRoles_TenantId",
                schema: "products",
                table: "UserTenantRoles",
                column: "TenantId");

            migrationBuilder.CreateIndex(
                name: "IX_UserTenantRoles_UserId",
                schema: "products",
                table: "UserTenantRoles",
                column: "UserId");

            migrationBuilder.CreateIndex(
                name: "IX_WarehouseLocation_TenantId",
                schema: "products",
                table: "WarehouseLocation",
                column: "TenantId");

            migrationBuilder.CreateIndex(
                name: "IX_WarehouseLocation_WarehouseId",
                schema: "products",
                table: "WarehouseLocation",
                column: "WarehouseId");

            migrationBuilder.CreateIndex(
                name: "IX_Warehouses_TenantId",
                schema: "products",
                table: "Warehouses",
                column: "TenantId");

            migrationBuilder.CreateIndex(
                name: "IX_WebhookDeliveries_WebhookId",
                schema: "products",
                table: "WebhookDeliveries",
                column: "WebhookId");

            migrationBuilder.CreateIndex(
                name: "IX_Webhooks_TenantId",
                schema: "products",
                table: "Webhooks",
                column: "TenantId");

            migrationBuilder.AddForeignKey(
                name: "FK_CouponUsages_Orders_OrderId",
                schema: "products",
                table: "CouponUsages",
                column: "OrderId",
                principalSchema: "products",
                principalTable: "Orders",
                principalColumn: "Id",
                onDelete: ReferentialAction.Restrict);

            migrationBuilder.AddForeignKey(
                name: "FK_InvoiceItems_Invoices_InvoiceId",
                schema: "products",
                table: "InvoiceItems",
                column: "InvoiceId",
                principalSchema: "products",
                principalTable: "Invoices",
                principalColumn: "Id",
                onDelete: ReferentialAction.Cascade);

            migrationBuilder.AddForeignKey(
                name: "FK_Invoices_Orders_OrderId",
                schema: "products",
                table: "Invoices",
                column: "OrderId",
                principalSchema: "products",
                principalTable: "Orders",
                principalColumn: "Id",
                onDelete: ReferentialAction.Restrict);
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropForeignKey(
                name: "FK_Coupons_Tenants_TenantId",
                schema: "products",
                table: "Coupons");

            migrationBuilder.DropForeignKey(
                name: "FK_Customers_Tenants_TenantId",
                schema: "products",
                table: "Customers");

            migrationBuilder.DropForeignKey(
                name: "FK_Invoices_Tenants_TenantId",
                schema: "products",
                table: "Invoices");

            migrationBuilder.DropForeignKey(
                name: "FK_Orders_Tenants_TenantId",
                schema: "products",
                table: "Orders");

            migrationBuilder.DropForeignKey(
                name: "FK_Resellers_Tenants_TenantId",
                schema: "products",
                table: "Resellers");

            migrationBuilder.DropForeignKey(
                name: "FK_Orders_Coupons_CouponId",
                schema: "products",
                table: "Orders");

            migrationBuilder.DropForeignKey(
                name: "FK_Orders_Customers_CustomerId",
                schema: "products",
                table: "Orders");

            migrationBuilder.DropForeignKey(
                name: "FK_Invoices_Orders_OrderId",
                schema: "products",
                table: "Invoices");

            migrationBuilder.DropTable(
                name: "ApiKeys",
                schema: "products");

            migrationBuilder.DropTable(
                name: "AuditLogs",
                schema: "products");

            migrationBuilder.DropTable(
                name: "CartItems",
                schema: "products");

            migrationBuilder.DropTable(
                name: "CouponCategories",
                schema: "products");

            migrationBuilder.DropTable(
                name: "CouponCustomers",
                schema: "products");

            migrationBuilder.DropTable(
                name: "CouponExcludedProducts",
                schema: "products");

            migrationBuilder.DropTable(
                name: "CouponProducts",
                schema: "products");

            migrationBuilder.DropTable(
                name: "CouponUsages",
                schema: "products");

            migrationBuilder.DropTable(
                name: "CustomerAddresses",
                schema: "products");

            migrationBuilder.DropTable(
                name: "Domains",
                schema: "products");

            migrationBuilder.DropTable(
                name: "EmailNotifications",
                schema: "products");

            migrationBuilder.DropTable(
                name: "InvoiceItems",
                schema: "products");

            migrationBuilder.DropTable(
                name: "MarketplaceIntegrations",
                schema: "products");

            migrationBuilder.DropTable(
                name: "NavigationMenus",
                schema: "products");

            migrationBuilder.DropTable(
                name: "NotificationLogs",
                schema: "products");

            migrationBuilder.DropTable(
                name: "OrderItems",
                schema: "products");

            migrationBuilder.DropTable(
                name: "PaymentProviders",
                schema: "products");

            migrationBuilder.DropTable(
                name: "ProductCategories",
                schema: "products");

            migrationBuilder.DropTable(
                name: "ProductImages",
                schema: "products");

            migrationBuilder.DropTable(
                name: "ProductInventories",
                schema: "products");

            migrationBuilder.DropTable(
                name: "ProductMetafields",
                schema: "products");

            migrationBuilder.DropTable(
                name: "ProductOptions",
                schema: "products");

            migrationBuilder.DropTable(
                name: "ResellerPrices",
                schema: "products");

            migrationBuilder.DropTable(
                name: "ReviewVotes",
                schema: "products");

            migrationBuilder.DropTable(
                name: "Shipments",
                schema: "products");

            migrationBuilder.DropTable(
                name: "TaxRules",
                schema: "products");

            migrationBuilder.DropTable(
                name: "TenantInvoiceSettings",
                schema: "products");

            migrationBuilder.DropTable(
                name: "UserTenantRoles",
                schema: "products");

            migrationBuilder.DropTable(
                name: "WebhookDeliveries",
                schema: "products");

            migrationBuilder.DropTable(
                name: "Carts",
                schema: "products");

            migrationBuilder.DropTable(
                name: "EmailProviders",
                schema: "products");

            migrationBuilder.DropTable(
                name: "EmailTemplates",
                schema: "products");

            migrationBuilder.DropTable(
                name: "Pages",
                schema: "products");

            migrationBuilder.DropTable(
                name: "ProductVariants",
                schema: "products");

            migrationBuilder.DropTable(
                name: "WarehouseLocation",
                schema: "products");

            migrationBuilder.DropTable(
                name: "ProductReviews",
                schema: "products");

            migrationBuilder.DropTable(
                name: "ShippingProviders",
                schema: "products");

            migrationBuilder.DropTable(
                name: "Categories",
                schema: "products");

            migrationBuilder.DropTable(
                name: "Users",
                schema: "products");

            migrationBuilder.DropTable(
                name: "Webhooks",
                schema: "products");

            migrationBuilder.DropTable(
                name: "Warehouses",
                schema: "products");

            migrationBuilder.DropTable(
                name: "Products",
                schema: "products");

            migrationBuilder.DropTable(
                name: "ProductTags",
                schema: "products");

            migrationBuilder.DropTable(
                name: "TaxRates",
                schema: "products");

            migrationBuilder.DropTable(
                name: "Tenants",
                schema: "products");

            migrationBuilder.DropTable(
                name: "Plans",
                schema: "products");

            migrationBuilder.DropTable(
                name: "Templates",
                schema: "products");

            migrationBuilder.DropTable(
                name: "Coupons",
                schema: "products");

            migrationBuilder.DropTable(
                name: "Customers",
                schema: "products");

            migrationBuilder.DropTable(
                name: "Orders",
                schema: "products");

            migrationBuilder.DropTable(
                name: "Invoices",
                schema: "products");

            migrationBuilder.DropTable(
                name: "Resellers",
                schema: "products");
        }
    }
}
