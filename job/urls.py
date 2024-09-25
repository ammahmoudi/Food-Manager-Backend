# job/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    JobViewSet,
    WorkflowViewSet,
)

# Create a router and register the viewsets for workflows and jobs
router = DefaultRouter()
router.register(r'workflows', WorkflowViewSet, basename='workflow')
router.register(r'jobs', JobViewSet, basename='job')

urlpatterns = [
    path('', include(router.urls)),  # All routes for workflows and jobs

]
