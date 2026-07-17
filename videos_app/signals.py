import os
from django.dispatch import receiver
from django.db.models.signals import post_delete, post_save
from .models import Video, VideoResolution


@receiver(post_save, sender=Video)
def create_lecture(sender, instance, created, **kwargs):
    if created:
        print('New object created')


@receiver(post_delete, sender=Video)
def auto_delete_video_files_on_delete(sender, instance, **kwargs):
    """
    Deletes original file when Video is deleted.
    VideoResolution files werden durch CASCADE automatisch gelöscht.
    """
    if instance.original_file:
        if os.path.isfile(instance.original_file.path):
            os.remove(instance.original_file.path)


@receiver(post_delete, sender=VideoResolution)
def auto_delete_resolution_file_on_delete(sender, instance, **kwargs):
    """
    Deletes converted resolution file from filesystem
    when corresponding VideoResolution object is deleted.
    """
    if instance.video_file:
        if os.path.isfile(instance.video_file.path):
            os.remove(instance.video_file.path)
