from rest_framework import serializers

from job.models.Dataset import Character, Dataset, DatasetImage


class DatasetImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = DatasetImage
        fields = ['id', 'name', 'image', 'complex_prompt', 'tag_prompt', 'negative_prompt', 'created_by', 'created_at']
        read_only_fields = ['created_by', 'created_at']


class DatasetSerializer(serializers.ModelSerializer):
    images = DatasetImageSerializer(many=True, required=False)

    class Meta:
        model = Dataset
        fields = ['id', 'name', 'created_by', 'created_at', 'images']
        read_only_fields = ['created_by', 'created_at']

    def create(self, validated_data):
        images_data = validated_data.pop('images', [])
        request = self.context.get('request')

        dataset = Dataset.objects.create(created_by=request.user, **validated_data)

        for image_data in images_data:
            DatasetImage.objects.create(dataset=dataset, created_by=request.user, **image_data)

        return dataset


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
