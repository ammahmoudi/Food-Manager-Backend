from django.urls import path, include
from rest_framework_nested import routers

from . import views
from utils.strings.url_names import U

router = routers.SimpleRouter()
router.register("push-notifications", views.PushNotificationViewSet, basename=U.V1_PUSH_NOTIFICATION)

urlpatterns = [
    path("", include(router.urls)),
 
]
