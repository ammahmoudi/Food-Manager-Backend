from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from pushNotification.models import FCMToken
from user.models import User
from user.serializers import UserSerializer
from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework import status

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    @action(detail=False, methods=["get"], url_path="check-phone-number")
    def check_phone_number(self, request):
        phone_number = request.query_params.get("phone_number")
        if not phone_number:
            return Response(
                {"detail": "Phone number is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        is_unique = not User.objects.filter(phone_number=phone_number).exists()
        return Response({"is_unique": is_unique}, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=["post"], url_path="subscribe-push")
    def subscribe_push_notifications(self, request):
        token = request.data.get("token", None)
        user = self.request.user

        if token:
            FCMToken.objects.update_or_create(user=user, token=token)
            return JsonResponse({"success": True, "message": "Push notification token stored"})
        return JsonResponse({"success": False, "message": "No token provided"})

    @action(detail=False, methods=["post"], url_path="unsubscribe-push")
    def unsubscribe_push_notifications(self, request):
        token = request.data.get("token", None)
        user = self.request.user

        if token:
            FCMToken.objects.filter(user=user, token=token).delete()
            return JsonResponse({"success": True, "message": "Push notification token removed"})
        return JsonResponse({"success": False, "message": "No token provided"})
