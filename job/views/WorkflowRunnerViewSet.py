from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiExample,
)
from job.models.Dataset import Character, Dataset, DatasetImage
from job.models.Job import Job
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
        # print(user_inputs)
        # print(input_mapping)
        for node_id, mappings in input_mapping.items():
            mapped_inputs[node_id] = {}
            for input_name, user_input_name in mappings.items():
                if user_input_name in user_inputs and input_name:
                    mapped_inputs[node_id][input_name] = user_inputs[user_input_name]

        return mapped_inputs

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
    def generate_character_initial_image(self, request):
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
        # print("request", request.data.get("inputs", {}))
        if "inputs" in request.data:
            mapped_inputs = self.map_inputs(request.data["inputs"], input_mapping)
        else:
            mapped_inputs = self.map_inputs(request.data, input_mapping)

        # Prepare the request for the run_workflow function
        # print(request.data)
        # print(input_mapping)
        request.data["inputs"] = mapped_inputs
        # print(mapped_inputs)
        #
        # Use the same workflow running logic
        return WorkflowViewSet()._run_workflow_logic(request, workflow)

    @extend_schema(
        operation_id="run_generate_character_sample",
        summary="Run jobs to generate character images and associate them with a dataset",
        description=(
            "This endpoint takes a user-provided image (specified by dataset_image_id) and compares it with reference images to generate character images. "
            "It generates character images using a specialized workflow and returns the dataset ID where all generated images are stored, along with job IDs."
        ),
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "dataset_image_id": {
                        "type": "integer",
                        "description": "ID of the user-provided dataset image used as a reference for generating character images.",
                    },
                },
                "required": ["dataset_image_id"],
                "example": {
                    "dataset_image_id": 123,
                },
            }
        },
        responses={
            200: OpenApiExample(
                "Success",
                value={
                    "dataset_id": 567,
                    "job_ids": [234, 235, 236],
                    "status": "started",
                },
                response_only=True,
            ),
            400: OpenApiExample(
                "Bad Request",
                value={"error": "Dataset image ID is required."},
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
                "Example Request",
                value={"dataset_image_id": 123},
                request_only=True,
            )
        ],
        tags=[
            "Workflow Runners"
        ],  # Add this tag to categorize under 'Workflow Runners'
    )
    @action(
        detail=False, methods=["post"], url_path="characters/generate-character-samples"
    )
    def generate_character_samples(self, request):
        dataset_image_id = request.data.get("dataset_image_id")
        if not dataset_image_id:
            return Response(
                {"error": "Dataset image ID is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user_image = DatasetImage.objects.get(id=dataset_image_id)
        except DatasetImage.DoesNotExist:
            return Response(
                {"error": "Dataset image not found."}, status=status.HTTP_404_NOT_FOUND
            )

        # Create a new dataset for this set of jobs
        new_dataset = Dataset.objects.create(
            name=f"Generated Character Dataset - {request.user.full_name}",
            created_by=request.user,
            character=user_image.character,
        )

        # Fetch reference dataset (jobs of the reference dataset will be used for generating samples)
        reference_dataset = Dataset.objects.get(name="face_test")

        # Get images from jobs of the reference dataset
        reference_images = []
        for image in reference_dataset.get_images().all():

            reference_images.append(image)

        if not reference_images:
            return Response(
                {"error": "No reference images found in the reference dataset."},
                status=status.HTTP_404_NOT_FOUND,
            )

        job_ids = []

        specialized_runner = self.get_runner("generate_character_sample")
        if not specialized_runner:
            return Response(
                {"error": "Specialized workflow runner not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Iterate over reference images and create jobs
        for reference_image in reference_images:
            mapped_inputs = {
                "user_image": user_image.get_full_image_url(request),
                "reference_image": reference_image.get_full_image_url(request),
            }
            # print(mapped_inputs)
            request.data["inputs"] = mapped_inputs

            # Prepare and run the workflow using shared logic
            response = self.prepare_and_run_workflow(request, specialized_runner)
            print(response)

            if response.status_code == status.HTTP_201_CREATED:
                job_id = response.data.get("job_id")
                job_ids.append(job_id)

                # Fetch the job object
                job = Job.objects.get(id=job_id)

                # Associate the job with the new dataset
                job.dataset = new_dataset
                job.save()

        return Response(
            {
                "message": "Jobs created successfully.",
                "dataset_id": new_dataset.id,
                "job_ids": job_ids,
            },
            status=status.HTTP_201_CREATED,
        )


    @extend_schema(
    operation_id="generate_character_image",
    summary="Generate a character image using the simple_flux_lora workflow",
    description=(
        "This endpoint takes a text prompt, character ID, and a LORA name to run the 'simple_flux_lora' workflow, "
        "extracting the LORA value from the character data to generate a customized character image. "
        "It returns the dataset ID where the image is stored and the associated job ID."
    ),
    request={
        "application/json": {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "Text prompt used for generating the character image.",
                },
                "character_id": {
                    "type": "integer",
                    "description": "ID of the character whose LORA data will be used.",
                },
                "lora_name": {
                    "type": "string",
                    "description": "Name of the LORA value to extract from the character data.",
                },
            },
            "required": ["prompt", "character_id", "lora_name"],
            "example": {
                "prompt": "A warrior standing in the rain",
                "character_id": 1,
                "lora_name": "elahe_final",
            },
        }
    },
    responses={
        200: OpenApiExample(
            "Success",
            value={
                "dataset_id": 567,
                "job_id": 123,
            },
            response_only=True,
        ),
        400: OpenApiExample(
            "Bad Request",
            value={"error": "Prompt, character_id, and lora_name are required."},
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
            "Example Request",
            value={
                "prompt": "A warrior standing in the rain",
                "character_id": 1,
                "lora_name": "elahe_final",
            },
            request_only=True,
        )
    ],
    tags=["Workflow Runners"],  # Add this tag to categorize under 'Workflow Runners'
)
    @action(detail=False, methods=["post"], url_path="characters/generate-character-image")
    def generate_character_image(self, request):
        # Get the specialized runner for the workflow
        specialized_runner = self.get_runner("generate_character_image")
        if not specialized_runner:
            return Response(
                {"error": "Specialized workflow runner not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Prepare the inputs (prompt, character_id, and lora_name)
        prompt = request.data.get("prompt")
        character_id = request.data.get("character_id")
        lora_name = request.data.get("lora_name")

        if not prompt or not character_id or not lora_name:
            return Response(
                {"error": "Prompt, character_id, and lora_name are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Retrieve the character instance
        try:
            character = Character.objects.get(id=character_id)
        except Character.DoesNotExist:
            return Response(
                {"error": "Character not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Retrieve the lora_value from the character's loras field
        lora_value = character.loras.get(lora_name)
        if not lora_value:
            return Response(
                {"error": f"LORA '{lora_name}' not found for the specified character."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Create a new dataset for this set of jobs
        dataset,is_new = Dataset.objects.get_or_create(
            name=f"Generated Character Dataset - {character_id} - {lora_name} - {request.user.full_name}",
            created_by=request.user,
            character=character,
            dataset_type="job"  # Assume this is a job-based dataset
        )

        # Prepare the input format required for the workflow
        input_data = {
            "prompt": prompt,
            "lora_value": lora_value,  # Include the lora_value in the inputs
        }

        # Pass the inputs to the workflow
        request.data["inputs"] = input_data

        # Use the same workflow running logic
        response = self.prepare_and_run_workflow(request, specialized_runner)

        if response.status_code == status.HTTP_201_CREATED:
            job_id = response.data.get("job_id")

            # Fetch the job object
            job = Job.objects.get(id=job_id)

            # Associate the job with the new dataset
            job.dataset = dataset
            job.save()

            return Response({
                "dataset_id": dataset.id,
                "job_id": job_id,
            }, status=status.HTTP_201_CREATED)

        return Response(
            {"error": "Failed to start the workflow."},
            status=status.HTTP_400_BAD_REQUEST,
        )
