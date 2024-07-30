from rest_framework import viewsets, permissions
from .models import User, Food, Meal, Comment
from .serializers import UserSerializer, FoodSerializer, MealSerializer, CommentSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
from persiantools.jdatetime import JalaliDate

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

    @action(detail=False, methods=['get'], url_path='filter/(?P<filter>[^/.]+)')
    def filter_meals(self, request, filter=None):
        now = timezone.now().date()
        if filter == 'upcoming':
            meals = Meal.objects.filter(date__gt=now)
        elif filter == 'past':
            meals = Meal.objects.filter(date__lt=now)
        elif filter == 'current_week':
            start_of_week = now - timedelta(days=now.weekday())
            end_of_week = start_of_week + timedelta(days=6)
            meals = Meal.objects.filter(date__range=[start_of_week, end_of_week])
        else:
            meals = Meal.objects.all()
        
        serializer = MealSerializer(meals, many=True, context={'request': request})
        return Response(serializer.data)
    
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
    
    @action(detail=False, methods=['get'], url_path='current-month')
    def get_meals_for_current_month(self, request):
        month_str = request.query_params.get('month', None)
        if month_str is None:
            return Response({'error': 'Month parameter is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            year, month = map(int, month_str.split('-'))
            start_of_month = JalaliDate(year, month, 1).to_gregorian()
            print(month)
            print(year)
            end_of_month_day = JalaliDate.days_in_month(month=month, year=year)
            end_of_month = JalaliDate(year, month, end_of_month_day).to_gregorian()
        except ValueError:
            return Response({'error': 'Invalid month parameter format. Use jYYYY-jMM'}, status=status.HTTP_400_BAD_REQUEST)

        meals = Meal.objects.filter(date__range=[start_of_month, end_of_month])
        serializer = self.get_serializer(meals, many=True, context={'request': request})
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
