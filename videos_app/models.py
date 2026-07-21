from django.db import models


class Video(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    original_file = models.FileField(upload_to='videos/original/')
    thumbnail_url = models.ImageField(
        upload_to='thumbnails/', null=True, blank=True)
    category = models.CharField(max_length=255, null=True, blank=True)
    is_processed = models.BooleanField(
        default=False, help_text="Alle Konvertierungen abgeschlossen")

    def __str__(self):
        return self.title


class VideoResolution(models.Model):
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
