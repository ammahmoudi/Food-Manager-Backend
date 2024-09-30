# job/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from job.views.DataSetViewSet import CharacterViewSet, DatasetImageViewSet, DatasetViewSet
from job.views.JobViewSet import JobViewSet
from job.views.WorkflowRunnerViewSet import WorkflowRunnerViewSet
from job.views.WorkflowViewSet import WorkflowViewSet


# Create a router and register the viewsets for workflows and jobs
router = DefaultRouter()
router.register(r'workflows', WorkflowViewSet, basename='workflow')
router.register(r'jobs', JobViewSet, basename='job')
router.register(r'workflow-runners', WorkflowRunnerViewSet, basename='Workflow Runner')
router.register(r'datasets', DatasetViewSet)
router.register(r'dataset-images', DatasetImageViewSet)
router.register(r'characters', CharacterViewSet)
urlpatterns = [
    path('', include(router.urls)),  # All routes for workflows and jobs

]
