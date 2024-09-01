from rest_framework import serializers

from utils.strings.field_names import S
from .models import User


class UserCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (S.ID, S.FULL_NAME, S.PHONE_NUMBER, "password", "role")
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class UserSerializer(serializers.ModelSerializer):
    remove_image = serializers.BooleanField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ("id", "full_name", "phone_number", "user_image", "role", "remove_image")

    def update(self, instance, validated_data):
        # Handle image removal
        if validated_data.get("remove_image"):
            instance.user_image.delete(save=False)
            validated_data.pop("remove_image")

        # Update the rest of the fields
        return super().update(instance, validated_data)
class PublicUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "full_name", "user_image", "role"]  # Exclude 'phone_number' or any other sensitive fields