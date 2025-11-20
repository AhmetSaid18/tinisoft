namespace Tinisoft.Application.Common.Interfaces;

public interface IImageProcessingService
{
    Task<ProcessedImageResult> ProcessImageAsync(
        Stream imageStream, 
        string fileName, 
        CancellationToken cancellationToken = default);
    
    Task<ProcessedImageResult> ProcessImageFromUrlAsync(
        string imageUrl, 
        string fileName, 
        CancellationToken cancellationToken = default);
}

public class ProcessedImageResult
{
    public string OriginalUrl { get; set; } = string.Empty;
    public long OriginalSizeBytes { get; set; }
    public int OriginalWidth { get; set; }
    public int OriginalHeight { get; set; }
    
    public string? ThumbnailUrl { get; set; } // 150x150
    public string? SmallUrl { get; set; } // 300x300
    public string? MediumUrl { get; set; } // 600x600
    public string? LargeUrl { get; set; } // 1200x1200
}

