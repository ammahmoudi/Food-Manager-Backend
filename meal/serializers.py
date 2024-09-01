from rest_framework import serializers
from user.serializers import PublicUserSerializer, UserSerializer
from .models import Food, Meal, Comment, Rate
from django.db.models import Avg


class FoodSerializer(serializers.ModelSerializer):
    meal_count = serializers.SerializerMethodField()
    avg_rate = (
        serializers.SerializerMethodField()
    )  # Add avg_rate as a SerializerMethodField

    class Meta:
        model = Food
        fields = [
            "id",
            "name",
            "image",
            "description",
            "avg_rate",
            "meal_count",
        ]

    def get_meal_count(self, obj):
        return Meal.objects.filter(food=obj).count()

    def get_avg_rate(self, obj):
        # Calculate the average rate of all meals associated with this food
        avg_rate = Meal.objects.filter(food=obj).aggregate(Avg("avg_rate"))[
            "avg_rate__avg"
        ]
        return round(avg_rate, 2) if avg_rate is not None else 0


class MealSerializer(serializers.ModelSerializer):
    food = FoodSerializer()
    date = serializers.DateField(format="%Y-%m-%d")
    avg_rate = (
        serializers.SerializerMethodField()
    )  # Add avg_rate as a SerializerMethodField

    class Meta:
        model = Meal
        fields = ["id", "date", "food", "avg_rate"]

    def get_avg_rate(self, obj):
        # Calculate the average rate of all rates associated with this meal
        avg_rate = Rate.objects.filter(meal=obj).aggregate(Avg("rate"))["rate__avg"]
        return round(avg_rate, 2) if avg_rate is not None else 0


class CreateMealSerializer(serializers.ModelSerializer):
    food_id = serializers.IntegerField()
    date = serializers.DateField()

    class Meta:
        model = Meal
        fields = ["food_id", "date"]

    def create(self, validated_data):
        food_id = validated_data.pop("food_id")
        food = Food.objects.get(id=food_id)
        meal = Meal.objects.create(food=food, **validated_data)
        return meal


class CommentCreateSerializer(serializers.ModelSerializer):
    meal_id = serializers.PrimaryKeyRelatedField(queryset=Meal.objects.all(), write_only=True, source='meal')

    class Meta:
        model = Comment
        fields = ['meal_id', 'text']

    def create(self, validated_data):
        request = self.context.get('request', None)
        if request and hasattr(request, 'user'):
            validated_data['user'] = request.user
        return super().create(validated_data)
    
class CommentUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['text']

    def update(self, instance, validated_data):
        instance.text = validated_data.get('text', instance.text)
        instance.save()
        return instance
class CommentDetailSerializer(serializers.ModelSerializer):
    user = PublicUserSerializer(read_only=True)
    meal = MealSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = [
            "id",
            "user",
            "meal",
            "text",
            "created_at",
            "updated_at"
        ]
        read_only_fields = ['created_at', 'updated_at', 'user', 'meal']

class RateSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Rate
        fields = ["id", "user", "meal", "rate", "created_at", "updated_at"]

    def create(self, validated_data):
        # Ensure a user can only rate a meal once
        rate, created = Rate.objects.update_or_create(
            user=self.context["request"].user,
            meal=validated_data.get("meal"),
            defaults={"rate": validated_data.get("rate")},
        )
        return rate
