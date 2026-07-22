import os
import django_rq
from django.dispatch import receiver
from django.db.models.signals import post_delete, post_save
from django.db import transaction
from .tasks import process_video_task
from .models import Video, VideoResolution


@receiver(post_save, sender=Video)
def trigger_video_processing(sender, instance, created, **kwargs):
    """Trigger video processing when a new video is uploaded and saved.

    When a Video object is created with an original_file, enqueues a
    video processing task to convert the video to multiple resolutions
    and generate an HLS playlist.

    Args:
        sender: The model class (Video)
        instance: The Video instance being saved
        created: Boolean indicating if this is a new object
        **kwargs: Additional keyword arguments
    """
    if created and instance.original_file:
        transaction.on_commit(
            lambda: django_rq.enqueue(process_video_task, instance.id)
        )


@receiver(post_delete, sender=Video)
def auto_delete_video_files_on_delete(sender, instance, **kwargs):
    """Delete original video file from filesystem when Video object is deleted.

    Removes the original uploaded video file when the associated Video
    model instance is deleted. VideoResolution files are automatically
    deleted by CASCADE on_delete behavior.

    Args:
        sender: The model class (Video)
        instance: The Video instance being deleted
        **kwargs: Additional keyword arguments
    """
    if instance.original_file:
        if os.path.isfile(instance.original_file.path):
            os.remove(instance.original_file.path)


@receiver(post_delete, sender=VideoResolution)
def auto_delete_resolution_file_on_delete(sender, instance, **kwargs):
    """Delete converted resolution video file when VideoResolution object is deleted.

    Removes the converted video file from the filesystem when the associated
    VideoResolution model instance is deleted.

    Args:
        sender: The model class (VideoResolution)
        instance: The VideoResolution instance being deleted
        **kwargs: Additional keyword arguments
    """
    if instance.video_file:
        if os.path.isfile(instance.video_file.path):
            os.remove(instance.video_file.path)
