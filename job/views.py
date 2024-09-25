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
from .tasks import run_workflow_task
from utils.cui import replace_user_inputs


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

            # Validate user inputs
            if not self.validate_inputs(workflow.inputs, user_inputs):
                return Response(
                    {"error": "Invalid inputs provided."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Create a job and run the workflow
            job = Job.objects.create(
                workflow=workflow,
                input_data=user_inputs,
                user=self.request.user,
                status="pending",
            )
            modified_workflow = replace_user_inputs(
                workflow.json_data, workflow.inputs, user_inputs
            )
            run_workflow_task.delay(job.id, modified_workflow)

            return Response({"job_id": job.id}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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

    def get_serializer(self, *args, **kwargs):
         # Pass the request context to the serializer
        kwargs['context'] = self.get_serializer_context()
        return super().get_serializer(*args, **kwargs)
    def perform_create(self, serializer):
        # Automatically assign the authenticated user
        serializer.save(user=self.request.user)
