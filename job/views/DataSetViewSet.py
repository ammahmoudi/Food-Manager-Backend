from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import serializers
from job.models.Dataset import Character, Dataset, DatasetImage
from job.models.Job import Job
from job.serializers.DatasetSeriallizers import AddImageToDatasetSerializer, CharacterSerializer, DatasetCreateSerializer, DatasetImageSerializer, DatasetSerializer, ImageDatasetSerializer, JobDatasetSerializer

@extend_schema_view(
    list=extend_schema(summary="List all datasets", tags=["Datasets"]),
    retrieve=extend_schema(summary="Retrieve a specific dataset", tags=["Datasets"]),
    create=extend_schema(summary="Create a new dataset", tags=["Datasets"]),
    update=extend_schema(summary="Update a dataset", tags=["Datasets"]),
    partial_update=extend_schema(summary="Partially update a dataset", tags=["Datasets"]),
    destroy=extend_schema(summary="Delete a dataset", tags=["Datasets"]),
)
class DatasetViewSet(viewsets.ModelViewSet):
    queryset = Dataset.objects.all()

    def get_serializer_class(self):
        """Determine which serializer to use based on dataset type."""
        if self.action == 'create':
            return DatasetCreateSerializer
        dataset = self.get_object()
        if dataset.dataset_type == 'image':
            return ImageDatasetSerializer
        elif dataset.dataset_type == 'job':
            return JobDatasetSerializer
        return super().get_serializer_class()  # Fallback if needed

    def create(self, request, *args, **kwargs):
        """Custom create method to handle dataset creation."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        summary="Add images to an existing dataset",
        description="Add new images to an existing dataset.",
        tags=["Datasets"],
        request=AddImageToDatasetSerializer(many=True),
        responses={
            200: "Images successfully added.",
            400: "Invalid data.",
        },
    )
    @action(detail=True, methods=["post"], url_path="add-images")
    def add_images(self, request, pk=None): 
        dataset = self.get_object()

        # Ensure this is an image-based dataset
        if dataset.dataset_type != 'image':
            return Response({"error": "This dataset does not accept images."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = AddImageToDatasetSerializer(data=request.data, many=True)
        if serializer.is_valid():
            images_added = []
            for image_data in serializer.validated_data:
                dataset_image = DatasetImage.objects.create(
                    dataset=dataset, created_by=request.user, **image_data
                )
                images_added.append(dataset_image)

            return Response({"status": "images added", "image_ids": [img.id for img in images_added]}, status=status.HTTP_200_OK)

        return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    @extend_schema(
        summary="Add jobs to an existing dataset",
        description="Add new jobs to an existing dataset.",
        tags=["Datasets"],
        request=serializers.PrimaryKeyRelatedField(queryset=Job.objects.all(), many=True),
        responses={200: "Jobs successfully added.", 400: "Invalid data."},
    )
    @action(detail=True, methods=["post"], url_path="add-jobs")
    def add_jobs(self, request, pk=None):
        dataset = self.get_object()
        job_ids = request.data.get('job_ids', [])

        for job_id in job_ids:
            try:
                job = Job.objects.get(id=job_id)
                job.dataset = dataset  # Associate the job with the dataset
                job.save()
            except Job.DoesNotExist:
                return Response({"error": f"Job {job_id} does not exist"}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"status": "Jobs added to dataset"}, status=status.HTTP_200_OK)

@extend_schema_view(
    list=extend_schema(summary="List all dataset images", tags=["Dataset Images"]),
    retrieve=extend_schema(summary="Retrieve a specific dataset image", tags=["Dataset Images"]),
    create=extend_schema(summary="Create a new dataset image", tags=["Dataset Images"]),
    update=extend_schema(summary="Update a dataset image", tags=["Dataset Images"]),
    partial_update=extend_schema(summary="Partially update a dataset image", tags=["Dataset Images"]),
    destroy=extend_schema(summary="Delete a dataset image", tags=["Dataset Images"]),
)
class DatasetImageViewSet(viewsets.ModelViewSet):
    queryset = DatasetImage.objects.all()
    serializer_class = DatasetImageSerializer


@extend_schema_view(
    list=extend_schema(summary="List all characters", tags=["Characters"]),
    retrieve=extend_schema(summary="Retrieve a specific character", tags=["Characters"]),
    create=extend_schema(summary="Create a new character", tags=["Characters"]),
    update=extend_schema(summary="Update a character", tags=["Characters"]),
    partial_update=extend_schema(summary="Partially update a character", tags=["Characters"]),
    destroy=extend_schema(summary="Delete a character", tags=["Characters"]),
)
class CharacterViewSet(viewsets.ModelViewSet):
    queryset = Character.objects.all()
    serializer_class = CharacterSerializer

    @extend_schema(
        summary="List all datasets for a character",
        description="Retrieve all datasets associated with a character.",
        tags=["Characters"],
    )
    @action(detail=True, methods=["get"], url_path="datasets")
    def get_character_datasets(self, request, pk=None):
        character = self.get_object()
        datasets = character.datasets.all()
        serializer = DatasetSerializer(datasets, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="List all images for a character",
        description="Retrieve all images associated with a character.",
        tags=["Characters"],
    )
    @action(detail=True, methods=["get"], url_path="images")
    def get_character_images(self, request, pk=None):
        character = self.get_object()
        images = character.images.all()
        serializer = DatasetImageSerializer(images, many=True)
        return Response(serializer.data)
