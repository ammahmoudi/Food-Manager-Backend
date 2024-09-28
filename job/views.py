import json
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema_view, extend_schema
from .models import Workflow, Job
from .serializers import (
    WorkflowCreateSerializer,
    WorkflowJSONSerializer,
    WorkflowSerializer,
    JobCreateSerializer,
    JobSerializer,
    RunWorkflowSerializer,
)
from .tasks import run_test, run_workflow_task
from utils.cui import replace_user_inputs
import os
import base64
from django.conf import settings
from PIL import Image
from django.core.files.storage import default_storage
from django.utils.timezone import now
from urllib.parse import urljoin
from django.core.files.uploadedfile import InMemoryUploadedFile


# Workflow viewset with API schema extensions for categorization
@extend_schema_view(
    list=extend_schema(summary="List all workflows", tags=["Workflows"]),
    retrieve=extend_schema(summary="Retrieve a specific workflow", tags=["Workflows"]),
    create=extend_schema(summary="Create a new workflow", tags=["Workflows"]),
    update=extend_schema(summary="Update a workflow", tags=["Workflows"]),
    partial_update=extend_schema(
        summary="Partially update a workflow", tags=["Workflows"]
    ),
    destroy=extend_schema(summary="Delete a workflow", tags=["Workflows"]),
)
class WorkflowViewSet(viewsets.ModelViewSet):
    queryset = Workflow.objects.all()

    def get_serializer_class(self):
        if self.action == "create":
            return WorkflowCreateSerializer
        return WorkflowSerializer

    def perform_create(self, serializer):
        # Automatically assign the authenticated user
        serializer.save(user=self.request.user)

    @extend_schema(
        summary="Run a workflow",
        request=RunWorkflowSerializer,
        responses={201: JobSerializer},
        tags=["Workflows"],
    )
    @action(detail=True, methods=["post"], url_path="run")
    def run_workflow(self, request, pk=None):
        workflow = self.get_object()
        serializer = RunWorkflowSerializer(data=request.data)
        
        if serializer.is_valid():
            user_inputs = serializer.validated_data.get("inputs", {})

            processed_inputs = {}  # This will store all processed inputs

            # Iterate through each node and its inputs
            for node_id, node_inputs in user_inputs.items():
                processed_inputs[node_id] = {}

                # Handle each input (string or image)
                for input_name, input_value in node_inputs.items():
                    # Determine the expected input type from the workflow data
                    expected_type = workflow.inputs.get(node_id, {}).get(input_name)

                    # If the input is a file (image), handle it accordingly
                    if isinstance(input_value, InMemoryUploadedFile):
                        if expected_type == "image_url":
                            # Save the image and return the URL
                            image_path = self.save_image(input_value, request.user, workflow)
                            processed_inputs[node_id][input_name] = image_path
                        elif expected_type == "image_base64":
                            # Convert the image to base64
                            image_base64 = self.convert_image_to_base64(input_value)
                            processed_inputs[node_id][input_name] = image_base64
                    elif isinstance(input_value, str):
                        # If it's a string input, simply assign it
                        processed_inputs[node_id][input_name] = input_value
                    else:
                        return Response(
                            {"error": f"Invalid input for {input_name} in node {node_id}"},
                            status=status.HTTP_400_BAD_REQUEST,
                        )

            # Validate inputs
            if not self.validate_inputs(workflow.inputs, processed_inputs):
                return Response(
                    {"error": "Invalid inputs provided."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Create a job and run the workflow
            job = Job.objects.create(
                workflow=workflow,
                input_data=processed_inputs,
                user=self.request.user,
                status="pending",
            )

            modified_workflow = replace_user_inputs(
                workflow.json_data, workflow.inputs, processed_inputs
            )

            run_workflow_task.delay(job.id, modified_workflow)
            return Response({"job_id": job.id}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def save_image(self, image_file, user, workflow):
        """Save image to a folder and return the URL."""
        user_dir = f"media/{user.id}/{workflow.id}/"
        if not os.path.exists(user_dir):
            os.makedirs(user_dir)

        image_path = os.path.join(user_dir, image_file.name)
        with open(image_path, 'wb') as f:
            for chunk in image_file.chunks():
                f.write(chunk)

        # Return the relative path as a URL (adjust based on your URL setup)
        return f"/media/{user.id}/{workflow.id}/{image_file.name}"

    def convert_image_to_base64(self, image_file):
        """Convert the image file to a base64-encoded string."""
        image_data = image_file.read()
        base64_str = base64.b64encode(image_data).decode('utf-8')
        return base64_str

    def validate_inputs(self, workflow_inputs, processed_inputs):
        """Validate if all necessary inputs are provided and correctly formatted."""
        for node_id, node_inputs in workflow_inputs.items():
            if node_id not in processed_inputs:
                return False
            for input_name in node_inputs:
                if input_name not in processed_inputs[node_id]:
                    return False
        return True
    def validate_inputs(self, workflow_inputs, user_inputs):
        for node_id, input_name in workflow_inputs.items():
            if node_id not in user_inputs:
                return False
        return True

    @extend_schema(
        summary="Parse and extract nodes from user-provided workflow JSON",
        request=WorkflowJSONSerializer,
        responses={200: dict},
        tags=["Workflows"],
    )
    @action(detail=False, methods=["post"], url_path="nodes")
    def parse_workflow_json(self, request):
        serializer = WorkflowJSONSerializer(data=request.data)
        if serializer.is_valid():
            workflow_data = serializer.validated_data["json_data"]

            # Check if the JSON data is a string and try to parse it
            if isinstance(workflow_data, str):
                try:
                    workflow_data = json.loads(workflow_data)
                except json.JSONDecodeError:
                    return Response(
                        {"error": "Invalid JSON format."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            nodes_list = self.extract_nodes_from_json(workflow_data)
            return Response(nodes_list, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def extract_nodes_from_json(self, workflow_data):
        nodes = []
        for node_id, node_info in workflow_data.items():
            node = {
                "id": node_id,
                "name": (
                    node_info["_meta"]["title"]
                    if "_meta" in node_info and "title" in node_info["_meta"]
                    else "Unknown"
                ),
                "type": (
                    node_info["class_type"] if "class_type" in node_info else "Unknown"
                ),
                "inputs": (
                    list(node_info["inputs"].keys()) if "inputs" in node_info else []
                ),
            }
            nodes.append(node)
        return nodes


# Job viewset with API schema extensions for categorization
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
