from rest_framework import viewsets, permissions
from rest_framework.decorators import action

from user.models import User
from user.serializers import UserSerializer
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status


# Create your views here.
class AdminCheckView(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"], url_path="admin_check")
    def get(self, request):
        user = request.user
        if user.is_admin:
            return Response({'is_admin': True}, status=status.HTTP_200_OK)
        return Response({'is_admin': False}, status=status.HTTP_403_FORBIDDEN)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
