from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema, extend_schema_view

from job.models.Dataset import Character, Dataset, DatasetImage
from job.serializers.DatasetSeriallizers import AddImageToDatasetSerializer, CharacterSerializer, DatasetImageSerializer, DatasetSerializer

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
    serializer_class = DatasetSerializer

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
        serializer = AddImageToDatasetSerializer(data=request.data, many=True)

        if serializer.is_valid():
            for image_data in serializer.validated_data:
                DatasetImage.objects.create(dataset=dataset, created_by=request.user, **image_data)

            return Response({"status": "images added"}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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
