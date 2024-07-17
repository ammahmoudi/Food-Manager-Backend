from django.contrib import admin
from .models import User, Food, Meal, Feedback

admin.site.register(User)
admin.site.register(Food)
admin.site.register(Meal)
admin.site.register(Feedback)
