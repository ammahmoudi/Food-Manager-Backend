from rest_framework import serializers

from job.models.Dataset import Character, Dataset, DatasetImage


class DatasetImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = DatasetImage
        fields = ['id', 'name', 'image','job' ,'complex_prompt', 'tag_prompt', 'negative_prompt', 'created_by', 'created_at']
        read_only_fields = ['created_by', 'created_at']
        
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get('request', None)
        # Add full URL for image if image exists
        if instance.image and request:
            representation['image_url'] = request.build_absolute_uri(instance.image.url)
        return representation
    
    def get_full_image_url(self, obj):
        """Returns the full image URL by using the request context."""
        request = self.context.get('request')
        if request:
            return obj.get_full_image_url(request)
        return None


class ImageDatasetSerializer(serializers.ModelSerializer):
    images = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Dataset
        fields = ['id', 'name', 'created_by', 'created_at', 'character', 'images']
class JobDatasetSerializer(serializers.ModelSerializer):
    jobs = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Dataset
        fields = ['id', 'name', 'created_by', 'created_at', 'character', 'jobs']


class DatasetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dataset
        fields = ['id', 'name', 'created_by', 'created_at', 'temporary', 'character', 'dataset_type']
class DatasetCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dataset
        fields = ['id', 'name', 'created_by', 'character', 'dataset_type']  # Include dataset_type field


class CharacterSerializer(serializers.ModelSerializer):
    datasets = DatasetSerializer(many=True, required=False)

    class Meta:
        model = Character
        fields = ['id', 'name', 'loras', 'image', 'datasets', 'created_by', 'created_at']
        read_only_fields = ['created_by', 'created_at']
class AddImageToDatasetSerializer(serializers.ModelSerializer):
    class Meta:
        model = DatasetImage
        fields = ['name', 'image', 'complex_prompt', 'tag_prompt', 'negative_prompt']

    def create(self, validated_data):
        request = self.context.get("request", None)
        if request and hasattr(request, "user"):
            validated_data["created_by"] = request.user
        return super().create(validated_data)
