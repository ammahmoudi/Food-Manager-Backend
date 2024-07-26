from rest_framework import viewsets, permissions
from .models import User, Food, Meal, Comment
from .serializers import UserSerializer, FoodSerializer, MealSerializer, CommentSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class FoodViewSet(viewsets.ModelViewSet):
    queryset = Food.objects.all()
    serializer_class = FoodSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @action(detail=True, methods=['get'])
    def comments(self, request, pk=None):
        food = self.get_object()
        meals = Meal.objects.filter(food=food)
        comments = Comment.objects.filter(meal__in=meals)
        serializer = CommentSerializer(comments, many=True,context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def meals(self, request, pk=None):
        food = self.get_object()
        meals = Meal.objects.filter(food=food)
        serializer = MealSerializer(meals, many=True, context={'request': request})
        return Response(serializer.data)

class MealViewSet(viewsets.ModelViewSet):
    queryset = Meal.objects.all()
    serializer_class = MealSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @action(detail=False, methods=['get'], url_path='date/(?P<date>[^/.]+)')
    def get_meal_by_date(self, request, date=None):
        try:
            meal = Meal.objects.get(date=date)
            serializer = self.get_serializer(meal,context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Meal.DoesNotExist:
            return Response({'error': 'Meal not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['get'])
    def comments(self, request, pk=None):
        meal = self.get_object()
        comments = meal.comment_set.all()
        serializer = CommentSerializer(comments, many=True,context={'request': request})
        return Response(serializer.data)

class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class AdminCheckView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.role == 'admin':
            return Response({'is_admin': True}, status=status.HTTP_200_OK)
        return Response({'is_admin': False}, status=status.HTTP_403_FORBIDDEN)
