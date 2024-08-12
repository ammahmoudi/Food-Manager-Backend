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
        # Check if the picture field is in the validated data and is empty
        if 'picture' in validated_data:
            picture = validated_data.get('picture')
            if picture == '' and instance.picture:
                # If picture is empty string, remove the existing image file
                instance.picture.delete(save=False)
                instance.picture = None
        else:
            instance.picture.delete(save=False)
            instance.picture = None

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
    userId = serializers.IntegerField(source='user.id', read_only=True)
    userName = serializers.CharField(source='user.name', read_only=True)
    userPicture = serializers.ImageField(source='user.user_image', read_only=True)
    mealName = serializers.CharField(source='meal.food.name', read_only=True)
    mealDate = serializers.DateField(source='meal.date', read_only=True)
    mealPicture = serializers.ImageField(source='meal.food.picture', read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'userId', 'userName', 'userPicture', 'text', 'mealName', 'mealDate', 'mealPicture']

