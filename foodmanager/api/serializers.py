from rest_framework import serializers
from .models import User, Food, Meal, Comment

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
    class Meta:
        model = Food
        fields = ['id', 'name', 'picture', 'description']

class MealSerializer(serializers.ModelSerializer):
    food = FoodSerializer()

    class Meta:
        model = Meal
        fields = ['id', 'date', 'food','rating']

class CommentSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    meal = MealSerializer()

    class Meta:
        model = Comment
        fields = ['id', 'user', 'meal', 'text',]
