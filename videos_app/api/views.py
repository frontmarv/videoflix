import os
from django.http import FileResponse, Http404
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from ..models import Video, VideoResolution
from .serializers import VideoSerializer


class VideoListView(generics.ListAPIView):
    """
    """
    queryset = Video.objects.all().order_by('-created_at')
    serializer_class = VideoSerializer
    permission_classes = [IsAuthenticated]


class HLSPlaylistView(APIView):
    """ Liefert die index.m3u8 aus. """
    permission_classes = [IsAuthenticated]

    def get(self, request, movie_id, resolution):
        try:
            video_res = VideoResolution.objects.get(
                video_id=movie_id, resolution=resolution)
        except VideoResolution.DoesNotExist:
            raise Http404(
                "Playlist nicht gefunden oder noch nicht konvertiert.")

        file_path = video_res.video_file.path
        if not os.path.exists(file_path):
            raise Http404("Datei existiert nicht auf dem Server.")

        return FileResponse(open(file_path, 'rb'), content_type='application/vnd.apple.mpegurl')


class HLSSegmentView(APIView):
    """ Liefert die einzelnen .ts Segmente aus. """
    permission_classes = [IsAuthenticated]

    def get(self, request, movie_id, resolution, segment):
        try:
            video_res = VideoResolution.objects.get(
                video_id=movie_id, resolution=resolution)
        except VideoResolution.DoesNotExist:
            raise Http404("Auflösung nicht gefunden.")

        base_dir = os.path.dirname(video_res.video_file.path)
        segment_path = os.path.join(base_dir, segment)

        if not os.path.abspath(segment_path).startswith(os.path.abspath(base_dir)):
            raise Http404("Ungültiger Dateipfad.")

        if not os.path.exists(segment_path):
            raise Http404("Segment nicht gefunden.")

        return FileResponse(open(segment_path, 'rb'), content_type='video/MP2T')
