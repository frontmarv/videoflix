from django.contrib import admin
from .models import Video, VideoResolution


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    """Admin interface for Video management with enhanced UI and functionality.

    Provides a complete admin interface for managing video uploads, viewing
    processing status, filtering by category and creation date, and managing
    associated video resolutions through inline editing.
    """
    list_display = [
        'title',
        'category',
        'is_processed',
        'created_at',
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

    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'category', 'created_at')
        }),
        ('Media', {
            'fields': ('original_file', 'thumbnail_url')
        }),
        ('Processing Status', {
            'fields': ('is_processed',)
        }),
    )

    readonly_fields = [
        'created_at',
        'is_processed',
    ]
