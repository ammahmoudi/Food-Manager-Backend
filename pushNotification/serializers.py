from rest_framework import serializers

from user.models import User
from .models import FCMToken, PushNotification

class FCMTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = FCMToken
        fields = ['id', 'user', 'token', 'created_at']

class PushNotificationSerializer(serializers.ModelSerializer):
    sent_tokens = FCMTokenSerializer(many=True, read_only=True)

    class Meta:
        model = PushNotification
        fields = ['id', 'title', 'message', 'image_url', 'link', 'sent_time', 'sent_tokens']

class PushNotificationRequestSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    message = serializers.CharField()
    link = serializers.URLField(required=False, allow_blank=True)
    user_ids = serializers.ListField(
        child=serializers.IntegerField(), required=False, allow_empty=True
    )
    image = serializers.ImageField(required=False,allow_null=True)
    
    def validate_image(self, value):
        # Ensure that a valid image file is provided
        if value and not hasattr(value, 'file'):
            raise serializers.ValidationError("Invalid file. Please upload a valid image.")
        return value
    def validate_user_ids(self, value):
        # Ensure user IDs are valid if provided
        if value and not User.objects.filter(id__in=value).exists():
            raise serializers.ValidationError("Some user IDs are invalid.")
        return value