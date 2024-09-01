from rest_framework import viewsets, permissions
from meal import models
from meal.models import Food, Meal, Comment, Rate
from meal.permissions import IsOwnerOrReadOnly
from meal.serializers import (
    CommentCreateSerializer,
    CommentDetailSerializer,
    CommentUpdateSerializer,
    CreateMealSerializer,
    FoodSerializer,
    MealSerializer,
    RateSerializer,
)
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
from persiantools.jdatetime import JalaliDate


class FoodViewSet(viewsets.ModelViewSet):
    queryset = Food.objects.all()
    serializer_class = FoodSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @action(detail=True, methods=["get"])
    def comments(self, request, pk=None):
        food = self.get_object()
        meals = Meal.objects.filter(food=food)
        comments = Comment.objects.filter(meal__in=meals)
        serializer = CommentDetailSerializer(
            comments, many=True, context={"request": request}
        )
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def meals(self, request, pk=None):
        food = self.get_object()
        meals = Meal.objects.filter(food=food)
        serializer = MealSerializer(meals, many=True, context={"request": request})
        return Response(serializer.data)


class MealViewSet(viewsets.ModelViewSet):
    queryset = Meal.objects.all()
    serializer_class = MealSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        if self.action == "create":
            return CreateMealSerializer
        if self.action == "update":
            return CreateMealSerializer

        return MealSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="filter/(?P<filter>[^/.]+)")
    def filter_meals(self, request, filter=None):
        now = timezone.now().date()
        if filter == "upcoming":
            meals = Meal.objects.filter(date__gt=now)
        elif filter == "past":
            meals = Meal.objects.filter(date__lt=now)
        elif filter == "current_week":
            start_of_week = now - timedelta(days=now.weekday())
            end_of_week = start_of_week + timedelta(days=6)
            meals = Meal.objects.filter(date__range=[start_of_week, end_of_week])
        else:
            meals = Meal.objects.all()

        serializer = MealSerializer(meals, many=True, context={"request": request})
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="date/(?P<date>[^/.]+)")
    def get_meal_by_date(self, request, date=None):
        try:
            meal = Meal.objects.get(date=date)
            serializer = self.get_serializer(meal, context={"request": request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Meal.DoesNotExist:
            return Response(
                {"error": "Meal not found"}, status=status.HTTP_404_NOT_FOUND
            )
    @action(detail=False, methods=['get'], url_path='current-month/(?P<month>[^/.]+)')
    def get_meals_for_current_month(self, request, month=None):
        if month is None:
            return Response({'error': 'Month parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            year, month = map(int, month.split('-'))
            start_of_month = JalaliDate(year, month, 1).to_gregorian()
            end_of_month_day = JalaliDate.days_in_month(month=month, year=year)
            end_of_month = JalaliDate(year, month, end_of_month_day).to_gregorian()
        except ValueError:
            return Response({'error': 'Invalid month parameter format. Use jYYYY-jMM'}, status=status.HTTP_400_BAD_REQUEST)

        meals = Meal.objects.filter(date__range=[start_of_month, end_of_month])
        serializer = self.get_serializer(meals, many=True, context={'request': request})
        return Response(serializer.data)
    @action(detail=True, methods=["get"])
    def comments(self, request, pk=None):
        meal = self.get_object()
        comments = Comment.objects.filter(meal=meal)
        serializer = CommentDetailSerializer(comments, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get", "post", "put", "delete"])
    def rate(self, request, pk=None):
        meal = self.get_object()
        if request.method == "POST":
            rate_value = request.data.get("rate", None)
            if rate_value is not None:
                rate, created = Rate.objects.update_or_create(
                    user=request.user,
                    meal=meal,
                    defaults={"rate": rate_value},
                )
                serializer = RateSerializer(rate)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(
                {"error": "Rate value is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        elif request.method == "PUT":
            rate = Rate.objects.filter(meal=meal, user=request.user).first()
            if rate:
                rate_value = request.data.get("rate", None)
                rate.rate = rate_value
                rate.save()
                serializer = RateSerializer(rate)
                return Response(serializer.data)
            return Response(
                {"error": "Rate not found"}, status=status.HTTP_404_NOT_FOUND
            )

        elif request.method == "DELETE":
            rate = Rate.objects.filter(meal=meal, user=request.user).first()
            if rate:
                rate.delete()
                return Response(
                    {"detail": "Rate deleted successfully"},
                    status=status.HTTP_204_NO_CONTENT,
                )
            return Response(
                {"error": "Rate not found"}, status=status.HTTP_404_NOT_FOUND
            )

        else:  # GET method
            rate = Rate.objects.filter(meal=meal, user=request.user).first()
            serializer = RateSerializer(rate)
            return Response(serializer.data)


class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    def get_serializer_class(self):
        if self.action == 'create':
            return CommentCreateSerializer
        elif self.action == 'update' or self.action == 'partial_update':
            return CommentUpdateSerializer
        return CommentDetailSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=["get"], permission_classes=[permissions.IsAdminUser])
    def latest(self, request):
        latest_comments = Comment.objects.order_by("-created_at")[:10]
        serializer = CommentDetailSerializer(latest_comments, many=True, context={'request': request})
        return Response(serializer.data)

class RateViewSet(viewsets.ModelViewSet):
    queryset = Rate.objects.all()
    serializer_class = RateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
