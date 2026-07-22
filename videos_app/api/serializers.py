from rest_framework import serializers
from ..models import Video, VideoResolution


class VideoResolutionSerializer(serializers.ModelSerializer):
    """Serializer for VideoResolution model.

    Provides serialization of video resolution objects containing resolution
    quality and the associated video file.
    """
    class Meta:
        model = VideoResolution
        fields = ['resolution', 'video_file']


class VideoSerializer(serializers.ModelSerializer):
    """Serializer for Video model list representation.

    Provides serialization of video metadata for list views and API responses.
    Excludes the large original_file and includes video creation metadata.
    """
    class Meta:
        model = Video
        fields = [
            'id',
            'created_at',
            'title',
            'description',
            'thumbnail_url',
            'category',
        ]
