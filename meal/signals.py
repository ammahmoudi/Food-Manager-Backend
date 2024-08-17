from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Rate, Meal, Food
from django.db.models import Avg

@receiver(post_save, sender=Rate)
@receiver(post_delete, sender=Rate)
def update_meal_avg_rate(sender, instance, **kwargs):
    meal = instance.meal
    if meal:
        # Calculate the average rate for the meal
        avg_rate = meal.rate_set.aggregate(Avg('rate'))['rate__avg'] or 0
        meal.avg_rate = avg_rate
        meal.save()

        # Update the avg_rate of the associated food
        update_food_avg_rate(meal.food)

def update_food_avg_rate(food):
    if food:
        # Calculate the average rate for the food based on its meals
        avg_rate = food.meal_set.aggregate(Avg('avg_rate'))['avg_rate__avg'] or 0
        food.avg_rate = avg_rate
        food.save()
