from django.db import models


class Video(models.Model):
    """Video model representing a video file with metadata and processing status.

    Stores information about uploaded videos including title, description,
    original file, thumbnail, and processing status for conversion into
    multiple resolutions.

    Attributes:
        id: Primary key (auto-generated).
        title: Video title.
        description: Detailed video description.
        created_at: Timestamp when video was uploaded.
        original_file: Path to original video file.
        thumbnail_url: Path to video thumbnail image.
        category: Optional video category for organization.
        is_processed: Indicates if all resolution conversions are complete.
    """
    CATEGORY_CHOICES = [
        ('action', 'Action'),
        ('comedy', 'Comedy'),
        ('drama', 'Drama'),
        ('horror', 'Horror'),
        ('scifi', 'Science Fiction'),
        ('animation', 'Animation'),
        ('documentary', 'Documentary'),
        ('romance', 'Romance'),
        ('thriller', 'Thriller'),
        ('adventure', 'Adventure'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    original_file = models.FileField(upload_to='videos/original/')
    thumbnail_url = models.ImageField(
        upload_to='thumbnails/', null=True, blank=True)
    category = models.CharField(
        max_length=50, choices=CATEGORY_CHOICES, null=True, blank=True)
    is_processed = models.BooleanField(
        default=False, help_text="All conversions to different resolutions are complete")

    class Meta:
        """Model metadata for Video."""
        verbose_name = "Video"
        verbose_name_plural = "Videos"
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class VideoResolution(models.Model):
    """Video resolution variant model for multi-resolution video delivery.

    Stores converted video files in different resolutions (480p, 720p, 1080p)
    to support adaptive bitrate streaming and provide video files optimized
    for different devices and network conditions.

    Attributes:
        video: Foreign key reference to parent Video object.
        resolution: Resolution quality choice (480p, 720p, or 1080p).
        video_file: Path to converted video file at this resolution.
        created_at: Timestamp when resolution conversion was created.
    """
    RESOLUTION_CHOICES = [
        ('480p', '480p'),
        ('720p', '720p'),
        ('1080p', '1080p'),
    ]

    video = models.ForeignKey(
        Video, on_delete=models.CASCADE, related_name='resolutions')
    resolution = models.CharField(max_length=5, choices=RESOLUTION_CHOICES)
    video_file = models.FileField(
        upload_to='videos/resolutions/')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('video', 'resolution')
        ordering = ['resolution']

    def __str__(self):
        return f"{self.video.title} - {self.resolution}"
