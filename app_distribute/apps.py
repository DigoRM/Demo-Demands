from django.apps import AppConfig


class AppDistributeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app_distribute'

    def ready(self):
        import app_distribute.signals
