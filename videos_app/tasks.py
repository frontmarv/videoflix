"""Video processing tasks for HLS streaming preparation.

These functions are designed to be executed by django-rq workers to process
uploaded videos into multiple resolutions optimized for adaptive bitrate streaming.
"""

import os
import subprocess
from django.conf import settings
from .models import Video, VideoResolution


def process_video_task(video_id):
    """Process a video into HLS-compatible multiple resolutions.

    Converts the original video file to 480p, 720p, and 1080p resolutions
    using FFmpeg, generates HLS playlists, and creates a thumbnail image.
    Updates the Video model's is_processed status upon completion.

    Args:
        video_id: ID of the Video object to process

    Raises:
        Video.DoesNotExist: If video with provided ID doesn't exist
        Exception: If FFmpeg conversion fails or file operations fail
    """
    try:
        video = Video.objects.get(id=video_id)
        input_path = video.original_file.path

        # Only auto-generate thumbnail if user hasn't uploaded one
        if not video.thumbnail_url:
            thumb_filename = f"thumb_{video_id}.jpg"
            thumb_rel_path = os.path.join('thumbnails', thumb_filename)
            thumb_abs_path = os.path.join(settings.MEDIA_ROOT, thumb_rel_path)
            os.makedirs(os.path.dirname(thumb_abs_path), exist_ok=True)

            subprocess.run([
                'ffmpeg', '-y', '-i', input_path,
                '-ss', '00:00:02.000', '-vframes', '1', thumb_abs_path
            ], capture_output=True, check=True)

            video.thumbnail_url = thumb_rel_path
            video.save(update_fields=['thumbnail_url'])

        resolutions = [
            ('480p', {'scale': '854:480', 'bitrate': '800k'}),
            ('720p', {'scale': '1280:720', 'bitrate': '2500k'}),
            ('1080p', {'scale': '1920:1080', 'bitrate': '5000k'}),
        ]

        for res, params in resolutions:
            res_rel_dir = os.path.join(
                'videos', 'resolutions', str(video_id), res)
            res_abs_dir = os.path.join(settings.MEDIA_ROOT, res_rel_dir)
            os.makedirs(res_abs_dir, exist_ok=True)

            playlist_abs_path = os.path.join(res_abs_dir, 'index.m3u8')
            playlist_rel_path = os.path.join(res_rel_dir, 'index.m3u8')
            segment_abs_path = os.path.join(res_abs_dir, 'segment_%03d.ts')

            hls_command = [
                'ffmpeg', '-y', '-i', input_path,
                '-vf', f'scale={params["scale"]}',
                '-c:v', 'libx264', '-b:v', params['bitrate'],
                '-c:a', 'aac', '-b:a', '128k',
                '-f', 'hls', '-hls_time', '10',
                '-hls_list_size', '0',
                '-hls_segment_filename', segment_abs_path,
                playlist_abs_path
            ]

            process_hls = subprocess.run(
                hls_command, capture_output=True, text=True)
            if process_hls.returncode != 0:
                raise Exception(f"Video conversion to {res} failed.")

            _update_m3u8_with_media_urls(playlist_abs_path, video_id, res)

            VideoResolution.objects.update_or_create(
                video=video,
                resolution=res,
                defaults={'video_file': playlist_rel_path}
            )

        video.is_processed = True
        video.save(update_fields=['is_processed'])

    except Exception as e:
        video.is_processed = False
        video.save(update_fields=['is_processed'])
        raise e


def _update_m3u8_with_media_urls(m3u8_path, video_id, resolution):
    """Update HLS playlist file with absolute API URLs for segments.

    Reads the generated m3u8 playlist file and replaces relative segment
    file paths with absolute API URLs. This allows clients to access
    video segments through the authenticated API endpoint.

    Example:
        Input:  segment_000.ts
        Output: /api/video/6/480p/segment_000.ts

    Args:
        m3u8_path: Absolute path to the m3u8 playlist file
        video_id: ID of the video
        resolution: Resolution string (480p, 720p, 1080p)

    Raises:
        Exception: If m3u8 file cannot be read or written
    """
    try:
        with open(m3u8_path, 'r') as f:
            content = f.read()

        lines = content.split('\n')
        updated_lines = []

        for line in lines:
            if line.strip().startswith('segment_'):
                segment_filename = line.strip()
                api_url = f"/api/video/{video_id}/{resolution}/{segment_filename}"
                updated_lines.append(api_url)
            else:
                updated_lines.append(line)
        with open(m3u8_path, 'w') as f:
            f.write('\n'.join(updated_lines))
    except Exception as e:
        raise Exception(f"Error updating m3u8 playlist file: {str(e)}")
