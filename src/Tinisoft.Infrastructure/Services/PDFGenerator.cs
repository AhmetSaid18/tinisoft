using QuestPDF.Fluent;
using QuestPDF.Helpers;
using QuestPDF.Infrastructure;
using Tinisoft.Domain.Entities;
using Tinisoft.Application.Invoices.Services;
using System.Text.Json;
using Microsoft.Extensions.Logging;

namespace Tinisoft.Infrastructure.Services;

/// <summary>
/// Fatura PDF oluşturma servisi
/// QuestPDF kullanarak profesyonel fatura PDF'leri oluşturur
/// </summary>
public class PDFGenerator : IPDFGenerator
{
    private readonly ILogger<PDFGenerator> _logger;

    public PDFGenerator(ILogger<PDFGenerator> logger)
    {
        _logger = logger;
        QuestPDF.Settings.License = LicenseType.Community; // Community license
    }

    public async Task<string> GenerateInvoicePDFAsync(
        Invoice invoice,
        TenantInvoiceSettings settings,
        CancellationToken cancellationToken = default)
    {
        _logger.LogInformation("Generating PDF for Invoice: {InvoiceNumber}", invoice.InvoiceNumber);

        try
        {
            // PDF document oluştur
            var pdfBytes = Document.Create(container =>
            {
                container.Page(page =>
                {
                    page.Size(PageSizes.A4);
                    page.Margin(2, Unit.Centimetre);
                    page.PageColor(Colors.White);
                    page.DefaultTextStyle(x => x.FontSize(10));

                    page.Header()
                        .Row(row =>
                        {
                            row.RelativeItem().Column(column =>
                            {
                                column.Item().Text($"FATURA NO: {invoice.InvoiceNumber}")
                                    .FontSize(16)
                                    .Bold()
                                    .FontColor(Colors.Blue.Medium);

                                column.Item().Text($"Seri: {invoice.InvoiceSerial}")
                                    .FontSize(10);

                                column.Item().PaddingTop(5).Text($"Tarih: {invoice.InvoiceDate:dd.MM.yyyy}")
                                    .FontSize(10);
                            });

                            row.RelativeItem().AlignRight().Column(column =>
                            {
                                if (!string.IsNullOrEmpty(settings.CompanyName))
                                {
                                    column.Item().Text(settings.CompanyName)
                                        .FontSize(14)
                                        .Bold();
                                }

                                if (!string.IsNullOrEmpty(settings.VKN))
                                {
                                    column.Item().Text($"VKN: {settings.VKN}")
                                        .FontSize(9);
                                }

                                if (!string.IsNullOrEmpty(settings.TaxOffice))
                                {
                                    column.Item().Text($"Vergi Dairesi: {settings.TaxOffice}")
                                        .FontSize(9);
                                }

                                if (!string.IsNullOrEmpty(settings.CompanyAddressLine1))
                                {
                                    column.Item().Text(settings.CompanyAddressLine1)
                                        .FontSize(9);
                                }

                                if (!string.IsNullOrEmpty(settings.CompanyCity))
                                {
                                    column.Item().Text($"{settings.CompanyPostalCode} {settings.CompanyCity}")
                                        .FontSize(9);
                                }

                                if (!string.IsNullOrEmpty(settings.CompanyPhone))
                                {
                                    column.Item().Text($"Tel: {settings.CompanyPhone}")
                                        .FontSize(9);
                                }

                                if (!string.IsNullOrEmpty(settings.CompanyEmail))
                                {
                                    column.Item().Text($"Email: {settings.CompanyEmail}")
                                        .FontSize(9);
                                }
                            });
                        });

                    page.Content()
                        .PaddingVertical(1, Unit.Centimetre)
                        .Column(column =>
                        {
                            column.Spacing(10);

                            // Müşteri Bilgileri
                            column.Item().PaddingBottom(10).BorderBottom(1).BorderColor(Colors.Grey.Lighten2)
                                .Column(customerColumn =>
                                {
                                    customerColumn.Item().Text("MÜŞTERİ BİLGİLERİ")
                                        .FontSize(12)
                                        .Bold()
                                        .FontColor(Colors.Blue.Medium);

                                    customerColumn.Item().Text(invoice.CustomerName)
                                        .FontSize(10)
                                        .Bold();

                                    if (!string.IsNullOrEmpty(invoice.CustomerVKN))
                                    {
                                        customerColumn.Item().Text($"VKN/TCKN: {invoice.CustomerVKN}")
                                            .FontSize(9);
                                    }

                                    if (!string.IsNullOrEmpty(invoice.CustomerTaxOffice))
                                    {
                                        customerColumn.Item().Text($"Vergi Dairesi: {invoice.CustomerTaxOffice}")
                                            .FontSize(9);
                                    }

                                    if (!string.IsNullOrEmpty(invoice.CustomerAddressLine1))
                                    {
                                        customerColumn.Item().Text(invoice.CustomerAddressLine1)
                                            .FontSize(9);
                                    }

                                    if (!string.IsNullOrEmpty(invoice.CustomerCity))
                                    {
                                        customerColumn.Item().Text($"{invoice.CustomerPostalCode} {invoice.CustomerCity}")
                                            .FontSize(9);
                                    }

                                    if (!string.IsNullOrEmpty(invoice.CustomerPhone))
                                    {
                                        customerColumn.Item().Text($"Tel: {invoice.CustomerPhone}")
                                            .FontSize(9);
                                    }

                                    if (!string.IsNullOrEmpty(invoice.CustomerEmail))
                                    {
                                        customerColumn.Item().Text($"Email: {invoice.CustomerEmail}")
                                            .FontSize(9);
                                    }
                                });

                            // Fatura Kalemleri
                            column.Item().Table(table =>
                            {
                                table.ColumnsDefinition(columns =>
                                {
                                    columns.ConstantColumn(40); // Sıra
                                    columns.RelativeColumn(3); // Açıklama
                                    columns.ConstantColumn(60); // Miktar
                                    columns.ConstantColumn(80); // Birim Fiyat
                                    columns.ConstantColumn(80); // KDV %
                                    columns.ConstantColumn(90); // KDV Tutarı
                                    columns.ConstantColumn(90); // Toplam
                                });

                                // Header
                                table.Header(header =>
                                {
                                    header.Cell().Element(CellStyle).Text("Sıra").Bold();
                                    header.Cell().Element(CellStyle).Text("Açıklama").Bold();
                                    header.Cell().Element(CellStyle).AlignCenter().Text("Miktar").Bold();
                                    header.Cell().Element(CellStyle).AlignRight().Text("Birim Fiyat").Bold();
                                    header.Cell().Element(CellStyle).AlignCenter().Text("KDV %").Bold();
                                    header.Cell().Element(CellStyle).AlignRight().Text("KDV Tutarı").Bold();
                                    header.Cell().Element(CellStyle).AlignRight().Text("Toplam").Bold();
                                });

                                // Items
                                foreach (var item in invoice.Items.OrderBy(i => i.Position))
                                {
                                    table.Cell().Element(CellStyle).Text(item.Position.ToString());
                                    table.Cell().Element(CellStyle).Text(item.ItemName);
                                    
                                    if (!string.IsNullOrEmpty(item.ItemDescription))
                                    {
                                        table.Cell().Element(CellStyle).Text(item.ItemDescription)
                                            .FontSize(8)
                                            .FontColor(Colors.Grey.Darken1);
                                    }

                                    table.Cell().Element(CellStyle).AlignCenter().Text(item.Quantity.ToString());
                                    table.Cell().Element(CellStyle).AlignRight().Text($"{item.UnitPrice:N2} {invoice.Currency}");
                                    table.Cell().Element(CellStyle).AlignCenter().Text($"{item.TaxRatePercent:F0}%");
                                    table.Cell().Element(CellStyle).AlignRight().Text($"{item.TaxAmount:N2} {invoice.Currency}");
                                    table.Cell().Element(CellStyle).AlignRight().Text($"{item.LineTotalWithTax:N2} {invoice.Currency}");
                                }
                            });

                            // Toplamlar
                            column.Item().PaddingTop(10).AlignRight().Column(totalColumn =>
                            {
                                totalColumn.Item().Row(row =>
                                {
                                    row.ConstantItem(150).Text("Ara Toplam:").Bold();
                                    row.ConstantItem(120).AlignRight().Text($"{invoice.Subtotal:N2} {invoice.Currency}");
                                });

                                totalColumn.Item().Row(row =>
                                {
                                    row.ConstantItem(150).Text("KDV Tutarı:").Bold();
                                    row.ConstantItem(120).AlignRight().Text($"{invoice.TaxAmount:N2} {invoice.Currency}");
                                });

                                if (invoice.DiscountAmount > 0)
                                {
                                    totalColumn.Item().Row(row =>
                                    {
                                        row.ConstantItem(150).Text("İndirim:").Bold();
                                        row.ConstantItem(120).AlignRight().Text($"-{invoice.DiscountAmount:N2} {invoice.Currency}")
                                            .FontColor(Colors.Red.Medium);
                                    });
                                }

                                if (invoice.ShippingAmount > 0)
                                {
                                    totalColumn.Item().Row(row =>
                                    {
                                        row.ConstantItem(150).Text("Kargo:").Bold();
                                        row.ConstantItem(120).AlignRight().Text($"{invoice.ShippingAmount:N2} {invoice.Currency}");
                                    });
                                }

                                totalColumn.Item().BorderTop(2).BorderColor(Colors.Blue.Medium).PaddingTop(5)
                                    .Row(row =>
                                    {
                                        row.ConstantItem(150).Text("GENEL TOPLAM:").FontSize(12).Bold().FontColor(Colors.Blue.Medium);
                                        row.ConstantItem(120).AlignRight().Text($"{invoice.Total:N2} {invoice.Currency}")
                                            .FontSize(12)
                                            .Bold()
                                            .FontColor(Colors.Blue.Medium);
                                    });
                            });

                            // Ödeme Bilgileri
                            if (!string.IsNullOrEmpty(invoice.PaymentMethod))
                            {
                                column.Item().PaddingTop(10).BorderTop(1).BorderColor(Colors.Grey.Lighten2)
                                    .Column(paymentColumn =>
                                    {
                                        paymentColumn.Item().Text("ÖDEME BİLGİLERİ")
                                            .FontSize(11)
                                            .Bold();

                                        paymentColumn.Item().Text($"Ödeme Yöntemi: {invoice.PaymentMethod}")
                                            .FontSize(9);

                                        if (invoice.PaymentDueDate.HasValue)
                                        {
                                            paymentColumn.Item().Text($"Vade: {invoice.PaymentDueDate.Value:dd.MM.yyyy}")
                                                .FontSize(9);
                                        }

                                        if (!string.IsNullOrEmpty(settings.IBAN))
                                        {
                                            paymentColumn.Item().Text($"IBAN: {settings.IBAN}")
                                                .FontSize(9);
                                        }
                                    });
                            }

                            // Notlar
                            if (!string.IsNullOrEmpty(invoice.Notes))
                            {
                                column.Item().PaddingTop(10).BorderTop(1).BorderColor(Colors.Grey.Lighten2)
                                    .Text($"Not: {invoice.Notes}")
                                    .FontSize(9)
                                    .FontColor(Colors.Grey.Darken1);
                            }

                            // GİB Bilgileri
                            if (!string.IsNullOrEmpty(invoice.GIBInvoiceId))
                            {
                                column.Item().PaddingTop(10).BorderTop(1).BorderColor(Colors.Grey.Lighten2)
                                    .Column(gibColumn =>
                                    {
                                        gibColumn.Item().Text("E-FATURA BİLGİLERİ")
                                            .FontSize(10)
                                            .Bold();

                                        gibColumn.Item().Text($"GİB Fatura ID: {invoice.GIBInvoiceId}")
                                            .FontSize(9);

                                        if (!string.IsNullOrEmpty(invoice.GIBInvoiceNumber))
                                        {
                                            gibColumn.Item().Text($"GİB Fatura No: {invoice.GIBInvoiceNumber}")
                                                .FontSize(9);
                                        }

                                        if (invoice.GIBSentAt.HasValue)
                                        {
                                            gibColumn.Item().Text($"Gönderim Tarihi: {invoice.GIBSentAt.Value:dd.MM.yyyy HH:mm}")
                                                .FontSize(9);
                                        }

                                        if (!string.IsNullOrEmpty(invoice.GIBApprovalStatus))
                                        {
                                            gibColumn.Item().Text($"Durum: {invoice.GIBApprovalStatus}")
                                                .FontSize(9)
                                                .FontColor(invoice.GIBApprovalStatus == "Onaylandı" 
                                                    ? Colors.Green.Medium 
                                                    : Colors.Red.Medium);
                                        }
                                    });
                            }
                        });

                    page.Footer()
                        .AlignCenter()
                        .Text("Bu fatura elektronik ortamda oluşturulmuştur, yasal geçerliliğe sahiptir.")
                        .FontSize(8)
                        .FontColor(Colors.Grey.Medium);
                });
            })
            .GeneratePdf();

            // PDF'i dosyaya kaydet (gerçek uygulamada blob storage'a upload edilir)
            var fileName = $"invoice-{invoice.InvoiceNumber}-{invoice.Id}.pdf";
            var directory = Path.Combine(Directory.GetCurrentDirectory(), "wwwroot", "invoices", "pdf");
            
            if (!Directory.Exists(directory))
            {
                Directory.CreateDirectory(directory);
            }

            var filePath = Path.Combine(directory, fileName);
            await File.WriteAllBytesAsync(filePath, pdfBytes, cancellationToken);

            var pdfUrl = $"/invoices/{invoice.Id}/pdf/{fileName}";

            _logger.LogInformation("PDF generated successfully for Invoice: {InvoiceNumber}, URL: {PDFUrl}", 
                invoice.InvoiceNumber, pdfUrl);

            return pdfUrl;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error generating PDF for Invoice: {InvoiceNumber}", invoice.InvoiceNumber);
            throw new InvalidOperationException("PDF oluşturma başarısız", ex);
        }
    }

    private static IContainer CellStyle(IContainer container)
    {
        return container
            .BorderBottom(0.5f)
            .BorderColor(Colors.Grey.Lighten2)
            .PaddingVertical(5)
            .PaddingHorizontal(5);
    }

    public async Task<string> GetTemplateAsync(
        Guid tenantId,
        string templateName = "default",
        CancellationToken cancellationToken = default)
    {
        // TODO: Tenant'a özel template getir (database'den veya dosya sisteminden)
        // Şimdilik default template
        return await Task.FromResult("default");
    }
}
