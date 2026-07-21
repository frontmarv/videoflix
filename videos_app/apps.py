from django.apps import AppConfig


class VideosAppConfig(AppConfig):
    name = 'videos_app'

    def ready(self):
        import videos_app.signals
