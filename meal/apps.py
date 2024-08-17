from django.apps import AppConfig


class MealConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "meal"
def ready(self):
        import meal.signals  # Import the signals to ensure they are connected
