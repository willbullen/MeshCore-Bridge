from django.apps import AppConfig


class MeshcoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.meshcore'
    verbose_name = 'MeshCore'
    
    def ready(self):
        import apps.meshcore.signals
