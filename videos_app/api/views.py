import os
from django.http import FileResponse, Http404
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from ..models import Video, VideoResolution
from .serializers import VideoSerializer


class VideoListView(generics.ListAPIView):
    """API endpoint for retrieving list of all videos.

    Provides a read-only list of videos ordered by creation date in
    descending order. Only authenticated users can access this endpoint.
    """
    queryset = Video.objects.all().order_by('-created_at')
    serializer_class = VideoSerializer
    permission_classes = [IsAuthenticated]


class HLSPlaylistView(APIView):
    """API endpoint for retrieving HLS playlist (index.m3u8) file.

    Serves the master playlist file for HTTP Live Streaming (HLS) video
    delivery at the requested resolution. Only authenticated users can access.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, movie_id, resolution):
        """Retrieve HLS playlist file for specified video and resolution.

        Args:
            request: HTTP request object.
            movie_id: ID of the video.
            resolution: Resolution variant (480p, 720p, or 1080p).

        Returns:
            FileResponse: HLS playlist file with media type application/vnd.apple.mpegurl.

        Raises:
            Http404: If video resolution not found or file doesn't exist on server.
        """
        try:
            video_res = VideoResolution.objects.get(
                video_id=movie_id, resolution=resolution)
        except VideoResolution.DoesNotExist:
            raise Http404(
                "Playlist not found or conversion in progress.")

        file_path = video_res.video_file.path
        if not os.path.exists(file_path):
            raise Http404("File does not exist on server.")

        return FileResponse(open(file_path, 'rb'), content_type='application/vnd.apple.mpegurl')


class HLSSegmentView(APIView):
    """API endpoint for retrieving individual HLS video segments (.ts files).

    Serves individual MPEG-2 Transport Stream (TS) segment files for HLS
    video streaming. Validates file paths to prevent directory traversal
    attacks. Only authenticated users can access.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, movie_id, resolution, segment):
        """Retrieve HLS video segment file.

        Args:
            request: HTTP request object.
            movie_id: ID of the video.
            resolution: Resolution variant (480p, 720p, or 1080p).
            segment: Segment filename to retrieve.

        Returns:
            FileResponse: Video segment file with media type video/MP2T.

        Raises:
            Http404: If resolution not found, invalid path, or segment doesn't exist.
        """
        try:
            video_res = VideoResolution.objects.get(
                video_id=movie_id, resolution=resolution)
        except VideoResolution.DoesNotExist:
            raise Http404("Resolution not found.")

        base_dir = os.path.dirname(video_res.video_file.path)
        segment_path = os.path.join(base_dir, segment)

        if not os.path.abspath(segment_path).startswith(os.path.abspath(base_dir)):
            raise Http404("Invalid file path.")

        if not os.path.exists(segment_path):
            raise Http404("Segment not found.")

        return FileResponse(open(segment_path, 'rb'), content_type='video/MP2T')
