import os
import subprocess
from django.conf import settings
from .models import Video, VideoResolution


def process_video_task(video_id):
    try:
        video = Video.objects.get(id=video_id)
        input_path = video.original_file.path

        thumb_filename = f"thumb_{video_id}.jpg"
        thumb_rel_path = os.path.join('thumbnails', thumb_filename)
        thumb_abs_path = os.path.join(settings.MEDIA_ROOT, thumb_rel_path)
        os.makedirs(os.path.dirname(thumb_abs_path), exist_ok=True)

        subprocess.run([
            'ffmpeg', '-y', '-i', input_path,
            '-ss', '00:00:02.000', '-vframes', '1', thumb_abs_path
        ], capture_output=True, check=True)

        video.thumbnail_url.name = thumb_rel_path
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
                raise Exception(f"Konvertierung {res} fehlgeschlagen")

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
    """
    Liest die m3u8-Datei und ersetzt relative Segment-Pfade 
    durch absolute API-URLs für authentifizierten Zugriff.

    Aus: segment_000.ts
    Zu:  /api/video/6/480p/segment_000.ts
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
        raise Exception(f"Fehler beim Aktualisieren der m3u8-Datei: {str(e)}")
