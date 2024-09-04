from django.urls import path, include
from rest_framework_nested import routers

from . import views
from utils.strings.url_names import U

router = routers.SimpleRouter()
router.register("users", views.UserViewSet, basename=U.V1_USER)

urlpatterns = [
    path("", include(router.urls)),
]
