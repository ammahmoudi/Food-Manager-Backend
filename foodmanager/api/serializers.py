from rest_framework import serializers
from .models import User, Food, Meal, Comment
from django.db.models import Avg


class UserCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'name', 'phone_number', 'password', 'role')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'name', 'phone_number', 'user_image', 'role')

class FoodSerializer(serializers.ModelSerializer):
    rating = serializers.SerializerMethodField()
    meal_count = serializers.SerializerMethodField()

    class Meta:
        model = Food
        fields = ['id', 'name', 'description', 'picture', 'rating', 'meal_count']

    def update(self, instance, validated_data):
        # Handle picture removal
        if 'remove_picture' in self.context['request'].data:
            if self.context['request'].data['remove_picture'] == 'true':
                instance.picture.delete(save=False)  # Remove the existing picture
                instance.picture = None

        # Handle picture update
        picture = validated_data.get('picture', None)

        if picture is None and 'picture' in validated_data:
            # If picture is None, the client might be trying to keep the existing picture,
            # so we should not remove the current picture unless explicitly requested
            validated_data.pop('picture', None)

        return super().update(instance, validated_data)

    def get_rating(self, obj):
        # Get all meals related to this food
        meals = Meal.objects.filter(food=obj)
        if meals.exists():
            # Calculate average rating
            average_rating = meals.aggregate(average=Avg('rating'))['average']
            return round(average_rating, 1) if average_rating else 0
        return 0

    def get_meal_count(self, obj):
        # Count all meals related to this food
        return Meal.objects.filter(food=obj).count()
class MealSerializer(serializers.ModelSerializer):
    food = FoodSerializer()
    date = serializers.DateField(format='%Y-%m-%d')  # Ensure standard date format
    class Meta:
        model = Meal
        fields = ['id', 'date', 'food','rating']
class CreateMealSerializer(serializers.ModelSerializer):
    food_id = serializers.IntegerField()
    date = serializers.DateField()

    class Meta:
        model = Meal
        fields = ['food_id', 'date']

    def create(self, validated_data):
        food_id = validated_data.pop('food_id')
        food = Food.objects.get(id=food_id)
        meal = Meal.objects.create(food=food, **validated_data)
        return meal


class CommentSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    meal = MealSerializer()

    class Meta:
        model = Comment
        fields = ['id', 'user', 'meal', 'text',]
