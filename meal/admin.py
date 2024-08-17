from django.contrib import admin

from meal.models import Food, Meal, Comment, Rate

admin.site.register(Food)
admin.site.register(Meal)
admin.site.register(Comment)
admin.site.register(Rate)