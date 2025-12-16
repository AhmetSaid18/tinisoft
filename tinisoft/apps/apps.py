from django.apps import AppConfig


class AppsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps'
    verbose_name = 'Tinisoft Apps'

    def ready(self):
        import apps.signals  # noqa

