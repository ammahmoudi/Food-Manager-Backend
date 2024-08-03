from django.contrib import admin

from meal.models import Food, Meal, Comment

admin.site.register(Food)
admin.site.register(Meal)
admin.site.register(Comment)