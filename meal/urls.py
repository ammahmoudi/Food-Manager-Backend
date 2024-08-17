from django.urls import path, include
from rest_framework_nested import routers

from . import views
from utils.strings.url_names import U

router = routers.SimpleRouter()
router.register("foods", views.FoodViewSet, basename=U.V1_FOOD)
router.register("meals", views.MealViewSet, basename=U.V1_MEAL)
router.register("comments", views.CommentViewSet, basename=U.V1_COMMENT)
router.register('rates', views.RateViewSet,basename=U.V1_RATE)

urlpatterns = [
    path("", include(router.urls)),
]
