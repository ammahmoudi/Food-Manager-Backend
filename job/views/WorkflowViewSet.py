import json
import re
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema_view, extend_schema
from job.models.Job import Job
from job.models.Workflow import Workflow
from job.serializers.JobSerializers import JobSerializer
from job.serializers.WorkflowSerializer import RunWorkflowSerializer, WorkflowCreateSerializer, WorkflowJSONSerializer, WorkflowSerializer
from job.tasks import run_workflow_task
from utils.cui import replace_user_inputs
import os
import base64


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
        return self._run_workflow_logic(request, workflow)

    def _run_workflow_logic(self, request, workflow):
        """The shared logic to run a workflow, used by both regular and specialized workflows."""
        serializer = RunWorkflowSerializer(data=request.data)

        if serializer.is_valid():
            user_inputs = serializer.validated_data.get("inputs", {})
            processed_inputs = self._prepare_inputs(workflow, user_inputs, request)

            if not self._validate_inputs(workflow.inputs, processed_inputs):
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

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def _prepare_inputs(self, workflow, user_inputs, request):
        """Prepare inputs for the workflow, processing base64 images, URLs, static paths, or other data."""
        processed_inputs = {}
        for node_id, node_inputs in user_inputs.items():
            processed_inputs[node_id] = {}
            for input_name, input_data in node_inputs.items():
                expected_type = workflow.inputs.get(node_id, {}).get(input_name, {})

                # Check if input is a base64 string (based on the pattern "data:image/*;base64,...")
                if expected_type == "image_url" and self.is_base64_image(input_data.get("input_value", "")):
                    image_url = self.save_base64_image(input_data["input_value"], request.user, workflow, request)
                    processed_inputs[node_id][input_name] = image_url

                # If input is already a URL or relative/static path
                elif expected_type == "image_url" and (input_data.get("input_value", "").startswith("http") or input_data.get("input_value", "").startswith("/")):
                    processed_inputs[node_id][input_name] = input_data["input_value"]

                # If expected type is base64, use the base64 image directly
                elif expected_type == "image_base64":
                    processed_inputs[node_id][input_name] = input_data["input_value"]

                # If expected type is string, use it as is
                elif expected_type == "string":
                    processed_inputs[node_id][input_name] = input_data["input_value"]

        return processed_inputs

    def is_base64_image(self, input_value):
        """Check if the input string is a base64-encoded image."""
        base64_pattern = re.compile(r"^data:image\/[a-zA-Z]+;base64,")
        return base64_pattern.match(input_value) is not None

    def _validate_inputs(self, workflow_inputs, processed_inputs):
        """Validate if all necessary inputs are provided and correctly formatted."""
        for node_id, node_inputs in workflow_inputs.items():
            if node_id not in processed_inputs:
                return False
            for input_name in node_inputs:
                if input_name not in processed_inputs[node_id]:
                    return False
        return True

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
