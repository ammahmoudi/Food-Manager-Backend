import json
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema_view, extend_schema
from .models import SpecializedWorkflowRunner, Workflow, Job
from .serializers import (
    SpecializedWorkflowRunnerSerializer,
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
            processed_inputs = {}  # Store the final processed inputs

            for node_id, node_inputs in user_inputs.items():
                processed_inputs[node_id] = {}

                for input_name, input_data in node_inputs.items():
                    expected_type = workflow.inputs.get(node_id, {}).get(input_name)[
                        "type"
                    ]

                    if expected_type == "image_url":
                        # Save the image as a file and get its full URL
                        image_path = self.save_base64_image(
                            input_data["input_value"], request.user, workflow, request
                        )
                        print("image url:", image_path)
                        processed_inputs[node_id][input_name] = image_path
                    elif expected_type == "image_base64":
                        # Use the base64 image directly
                        processed_inputs[node_id][input_name] = input_data[
                            "input_value"
                        ]
                        print("image base64:")
                    elif expected_type == "string":
                        processed_inputs[node_id][input_name] = input_data[
                            "input_value"
                        ]

            # Validate inputs and run the workflow
            if not self.validate_inputs(workflow.inputs, processed_inputs):
                return Response(
                    {"error": "Invalid inputs provided."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Create the job and run the workflow
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

    def save_base64_image(self, image_base64, user, workflow, request):
        """Save base64-encoded image to a file and return the full URL."""
        user_dir = f"media/user_{user.id}/w_{workflow.id}/"
        if not os.path.exists(user_dir):
            os.makedirs(user_dir)

        # Extract image format (assuming data:image/jpeg;base64,... or similar)
        format, imgstr = image_base64.split(";base64,")
        ext = format.split("/")[-1]  # Extract the file extension (e.g., jpg, png)

        # Generate a unique file name
        file_name = f"{user.id}_{workflow.id}_{self.generate_random_filename()}.{ext}"
        file_path = os.path.join(user_dir, file_name)

        # Decode the base64 string and save it as an image file
        with open(file_path, "wb") as f:
            f.write(base64.b64decode(imgstr))

        # Get the full URL of the saved image
        relative_url = f"/media/user_{user.id}/w_{workflow.id}/{file_name}"
        full_url = request.build_absolute_uri(relative_url)

        return full_url

    def generate_random_filename(self):
        """Generate a random string for file names."""
        import uuid

        return str(uuid.uuid4())

    def convert_image_to_base64(self, image_file):
        """Convert the image file to a base64-encoded string."""
        image_data = image_file.read()
        base64_str = base64.b64encode(image_data).decode("utf-8")
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


class SpecializedWorkflowRunnerViewSet(viewsets.ModelViewSet):
    queryset = SpecializedWorkflowRunner.objects.all()
    serializer_class = SpecializedWorkflowRunnerSerializer

    @action(detail=True, methods=["post"], url_path="run")
    def run_specialized_workflow(self, request, pk=None):
        specialized_runner = self.get_object()
        workflow = specialized_runner.workflow
        input_mapping = specialized_runner.input_mapping

        # Validate user inputs
        serializer = RunWorkflowSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user_inputs = serializer.validated_data.get("inputs", {})
        processed_inputs = self.prepare_inputs(user_inputs, input_mapping, workflow)

        # Validate and run the workflow
        if not self.validate_inputs(workflow.inputs, processed_inputs):
            return Response(
                {"error": "Invalid inputs provided."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create job and run workflow
        job = Job.objects.create(
            workflow=workflow,
            input_data=processed_inputs,
            user=request.user,
            status="pending",
        )

        modified_workflow = replace_user_inputs(
            workflow.json_data, workflow.inputs, processed_inputs
        )
        run_workflow_task.delay(job.id, modified_workflow)

        return Response({"job_id": job.id}, status=status.HTTP_201_CREATED)

    def prepare_inputs(self, user_inputs, input_mapping, workflow):
        processed_inputs = {}
        for node_id, node_inputs in input_mapping.items():
            processed_inputs[node_id] = {}
            for input_name, api_input_name in node_inputs.items():
                # Get the input from user inputs
                if api_input_name in user_inputs:
                    processed_inputs[node_id][input_name] = user_inputs[api_input_name]
        return processed_inputs

    def validate_inputs(self, workflow_inputs, processed_inputs):
        """Validate if all necessary inputs are provided and correctly formatted."""
        for node_id, node_inputs in workflow_inputs.items():
            if node_id not in processed_inputs:
                return False
            for input_name in node_inputs:
                if input_name not in processed_inputs[node_id]:
                    return False
        return True

    @action(detail=False, methods=["post"], url_path="characters/prompt")
    def generate_character_image(self, request):
        specialized_runner = SpecializedWorkflowRunner.objects.get(
            name="Generate Character Image from Prompt"
        )
        return self.run_specialized_workflow(request, specialized_runner.pk)


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
