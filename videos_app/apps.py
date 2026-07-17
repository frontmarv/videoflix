from django.apps import AppConfig


class VideosAppConfig(AppConfig):
    name = 'videos_app'

    def ready(self):
        from . import signals
