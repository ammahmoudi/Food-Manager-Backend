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
    def update(self, instance, validated_data):
        # Check if the picture field is in the validated data and is empty
        if 'picture' in validated_data:
            picture = validated_data.get('picture')
            if picture == '' and instance.picture:
                # If picture is empty string, remove the existing image file
                instance.picture.delete(save=False)
                # instance.picture.save('food_pictures/default.jpeg', None)
                instance.picture=None
        else :
            instance.picture.delete(save=False)
            # instance.picture.save('food_pictures/default.jpeg', None)
            instance.picture=None


        return super().update(instance, validated_data)

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
