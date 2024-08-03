from rest_framework import serializers

from user.serializers import UserSerializer
from .models import Food, Meal, Comment


class FoodSerializer(serializers.ModelSerializer):
    class Meta:
        model = Food
        fields = ['id', 'name', 'picture', 'description']


class MealSerializer(serializers.ModelSerializer):
    food = FoodSerializer()
    date = serializers.DateField(format='%Y-%m-%d')  # Ensure standard date format

    class Meta:
        model = Meal
        fields = ['id', 'date', 'food', 'rating']


class CommentSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    meal = MealSerializer()

    class Meta:
        model = Comment
        fields = ['id', 'user', 'meal', 'text', ]
