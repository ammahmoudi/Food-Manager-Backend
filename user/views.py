from rest_framework import viewsets, permissions
from rest_framework.decorators import action

from user.models import User
from user.serializers import UserSerializer
from rest_framework.response import Response
from rest_framework import status


# Create your views here.



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
