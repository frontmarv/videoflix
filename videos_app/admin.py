from django.contrib import admin
from .models import Video, VideoResolution


class VideoResolutionInline(admin.TabularInline):
    """Inline admin for managing video resolutions directly from Video admin."""
    model = VideoResolution
    extra = 1
    fields = ['resolution', 'video_file', 'created_at']
    readonly_fields = ['created_at']

    def get_queryset(self, request):
        """Order resolutions by resolution choice."""
        qs = super().get_queryset(request)
        return qs.order_by('resolution')


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    """Admin interface for Video management with enhanced UI and functionality."""

    list_display = [
        'title',
        'category',
    ]

    list_filter = [
        'category',
        'is_processed',
        'created_at',
    ]

    search_fields = [
        'title',
        'description',
        'category'
    ]

    readonly_fields = [
        'created_at',
        'is_processed',
    ]
