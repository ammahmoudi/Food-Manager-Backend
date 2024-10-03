import os
from rest_framework import viewsets
from rest_framework import permissions
from rest_framework.decorators import action
from django.http import JsonResponse

from user.models import User
from .models import PushNotification, FCMToken
from .serializers import PushNotificationRequestSerializer, PushNotificationSerializer
from utils.firebase import send_push_notification
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from rest_framework import status
from rest_framework.response import Response


class PushNotificationViewSet(viewsets.ModelViewSet):
    queryset = PushNotification.objects.all()
    serializer_class = PushNotificationSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @action(detail=False, methods=["post"], url_path="send")
    def send_push_notification(self, request):
        # Use the request serializer to validate input
        serializer = PushNotificationRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        title = serializer.validated_data.get("title")
        message = serializer.validated_data.get("message")
        link = serializer.validated_data.get("link")
        user_ids = serializer.validated_data.get("user_ids", None)  # List of user IDs
        image = serializer.validated_data.get('image',None)
        if not message:
            return JsonResponse({"success": False, "message": "No message provided"})

        # Create the notification
        notification = PushNotification.objects.create(
            title=title, message=message, link=link
        )

        # Handle image saving if provided
        if image:
            image_name = urlsafe_base64_encode(force_bytes(image.name))+'.png'
            image_path = os.path.join("push_notifications", image_name)
            full_image_path = default_storage.save(
                image_path, ContentFile(image.read())
            )
            notification.image_url = request.build_absolute_uri(
                default_storage.url(full_image_path)
            )
            notification.save()

        # Fetch the specified users or all users if no IDs are provided
        users = User.objects.filter(id__in=user_ids) if user_ids else User.objects.all()

        # Retrieve tokens for the users and send notifications
        for user in users:
            fcm_tokens = user.get_fcm_tokens()
            for fcm_token in fcm_tokens:
                try:
                    send_push_notification(
                        fcm_token.token, title, message, notification.image_url, link
                    )
                    token_obj = FCMToken.objects.get(token=fcm_token.token)
                    notification.sent_tokens.add(token_obj)
                except Exception as e:
                    print(f"Error sending notification to token {fcm_token.token}: {e}")

        notification.save()
        return JsonResponse({"success": True, "message": "Push notification sent"})
