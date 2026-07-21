from rest_framework import serializers
from ..models import Video, VideoResolution


class VideoResolutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoResolution
        fields = ['resolution', 'video_file']


class VideoSerializer(serializers.ModelSerializer):
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
