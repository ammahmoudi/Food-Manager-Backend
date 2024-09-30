# Job viewset with API schema extensions for categorization
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema_view, extend_schema
from job.models.Job import Job
from job.serializers.JobSerializers import JobCreateSerializer, JobSerializer

@extend_schema_view(
    list=extend_schema(summary="List all jobs", tags=["Jobs"]),
    retrieve=extend_schema(summary="Retrieve a specific job", tags=["Jobs"]),
    create=extend_schema(summary="Create a new job", tags=["Jobs"]),
    update=extend_schema(summary="Update a job", tags=["Jobs"]),
    partial_update=extend_schema(summary="Partially update a job", tags=["Jobs"]),
    destroy=extend_schema(summary="Delete a job", tags=["Jobs"]),
)
class JobViewSet(viewsets.ModelViewSet):
    queryset = Job.objects.all()

    def get_serializer_class(self):
        # Use different serializers for creating and retrieving jobs
        if self.action == "create":
            return JobCreateSerializer
        return JobSerializer

    def get_serializer(self, *args, **kwargs):
        # Pass the request context to the serializer
        kwargs["context"] = self.get_serializer_context()
        return super().get_serializer(*args, **kwargs)

    def perform_create(self, serializer):
        # Automatically assign the authenticated user
        serializer.save(user=self.request.user)

    # Custom action to get the job status
    @extend_schema(summary="Get job status", tags=["Jobs"])
    @action(detail=True, methods=["get"], url_path="status")
    def get_status(self, request, pk=None):
        job = self.get_object()
        return Response({"status": job.status}, status=status.HTTP_200_OK)

    # Custom action to get the job result
    @extend_schema(summary="Get job result", tags=["Jobs"])
    @action(detail=True, methods=["get"], url_path="result")
    def get_result(self, request, pk=None):
        job = self.get_object()
        return Response({"result_data": job.result_data}, status=status.HTTP_200_OK)

    # Custom action to get the job logs
    @extend_schema(summary="Get job logs", tags=["Jobs"])
    @action(detail=True, methods=["get"], url_path="log")
    def get_logs(self, request, pk=None):
        job = self.get_object()
        return Response({"logs": job.logs}, status=status.HTTP_200_OK)
