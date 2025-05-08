from django.apps import AppConfig

class MySiteConfig(AppConfig):
    name = "catalog"

    def ready(self):
        import catalog.signals
