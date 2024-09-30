from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiExample,
)

from job.models.WorkflowRunner import WorkflowRunner
from job.serializers.WorkflowRunnerSerializers import WorkflowRunnerSerializer
from job.views.WorkflowViewSet import WorkflowViewSet


@extend_schema_view(
    list=extend_schema(summary="List all Workflow Runners", tags=["Workflow Runners"]),
    retrieve=extend_schema(
        summary="Retrieve a specific Workflow Runner", tags=["Workflow Runners"]
    ),
    create=extend_schema(
        summary="Create a new Workflow Runner", tags=["Workflow Runners"]
    ),
    update=extend_schema(summary="Update a Workflow Runner", tags=["Workflow Runners"]),
    partial_update=extend_schema(
        summary="Partially update a Workflow Runner", tags=["Workflow Runners"]
    ),
    destroy=extend_schema(
        summary="Delete a Workflow Runner", tags=["Workflow Runners"]
    ),
)
class WorkflowRunnerViewSet(viewsets.ModelViewSet):
    queryset = WorkflowRunner.objects.all()
    serializer_class = WorkflowRunnerSerializer

    @extend_schema(
        operation_id="generate_character_image",
        summary="Generate a character image from a prompt",
        description="This endpoint takes a text prompt and uses the specialized workflow to generate a character image.",
        request=WorkflowRunnerSerializer,
        responses={
            200: OpenApiExample(
                "Success",
                value={"job_id": 123, "status": "started"},
                response_only=True,
            ),
            404: OpenApiExample(
                "Not Found",
                value={"error": "Specialized workflow runner not found."},
                response_only=True,
            ),
        },
        examples=[
            OpenApiExample(
                "Example",
                value={"prompt": "A warrior with a sword standing on a mountain"},
                request_only=True,
            )
        ],
        tags=[
            "Workflow Runners"
        ],  # Add this tag to categorize under 'Specialized Workflows'
    )
    @action(detail=False, methods=["post"], url_path="characters/prompt")
    def generate_character_image(self, request):
        specialized_runner = self.get_runner(
            "generate_character_initial_image_with_prompt"
        )
        if not specialized_runner:
            return Response(
                {"error": "Specialized workflow runner not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Prepare inputs and run the workflow
        return self.prepare_and_run_workflow(request, specialized_runner)

    def prepare_and_run_workflow(self, request, specialized_runner):
        """
        Prepare the inputs from the request for the workflow and run it.

        Args:
            request: The original request object.
            specialized_runner: The specialized workflow runner instance.

        Returns:
            Response: The response from running the workflow.
        """
        workflow = specialized_runner.workflow

        # Map inputs from request to the expected format
        input_mapping = (
            specialized_runner.input_mapping
        )  # Assuming this is a JSONField or similar
        print("request", request.data.get("inputs", {}))

        mapped_inputs = self.map_inputs(request.data, input_mapping)

        # Prepare the request for the run_workflow function

        request.data["inputs"] = mapped_inputs

        # Use the same workflow running logic
        return WorkflowViewSet()._run_workflow_logic(request, workflow)

    def get_runner(self, name):
        """Retrieve the specialized workflow runner by name."""
        try:
            return WorkflowRunner.objects.get(name=name)
        except WorkflowRunner.DoesNotExist:
            return None

    def map_inputs(self, user_inputs, input_mapping):
        """
        Map user inputs to the format required by the workflow based on the specialized input mapping.

        Args:
            user_inputs (dict): The inputs provided by the user in the request.
            input_mapping (dict): The mapping that specifies how to transform user inputs.

        Returns:
            dict: The transformed inputs ready for the workflow.
        """
        mapped_inputs = {}
        print(user_inputs)
        print(input_mapping)
        for node_id, mappings in input_mapping.items():
            mapped_inputs[node_id] = {}
            for input_name, user_input_name in mappings.items():
                if user_input_name in user_inputs and input_name:
                    mapped_inputs[node_id][input_name] = user_inputs[user_input_name]

        return mapped_inputs
