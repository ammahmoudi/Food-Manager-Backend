from rest_framework import serializers
from .models import Workflow, Job
from rest_framework import serializers
from django.conf import settings
from urllib.parse import urljoin
from rest_framework import serializers
from .models import Workflow, Job

class JobSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = ['id', 'workflow', 'status', 'runtime', 'result_data', 'input_data', 'logs', 'user']

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        # Convert relative URLs to full URLs in result_data
        request = self.context.get('request')
        if 'result_data' in representation and 'image_urls' in representation['result_data']:
            image_urls = representation['result_data']['image_urls']
            full_image_urls = []
            for url in image_urls:
                # Check if it's a relative URL and convert it to a full URL
                if not url.startswith('http'):
                    full_url = urljoin(request.build_absolute_uri('/'), url.lstrip('/'))
                    full_image_urls.append(full_url)
                else:
                    full_image_urls.append(url)

            # Update the result_data with full URLs
            representation['result_data']['image_urls'] = full_image_urls

        return representation
class JobCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = ['workflow', 'input_data']

    def create(self, validated_data):
        # Set the user from the request context
        request = self.context.get("request", None)
        if request and hasattr(request, "user"):
            validated_data["user"] = request.user
        return super().create(validated_data)

class WorkflowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workflow
        fields = ['id', 'name', 'json_data', 'last_modified', 'inputs', 'user']

class RunWorkflowSerializer(serializers.Serializer):
    inputs = serializers.DictField(
        child=serializers.DictField(
            child=serializers.FileField(allow_empty_file=False, required=False),  # Can be a file
            help_text="Each node input can either be a string or an image file.",
        ),
        help_text="Inputs with node IDs, where each node has its respective input values (strings or image files).",
    )
    
    def validate_inputs(self, data):
        # You can add further validation logic here if necessary, such as validating the input types
        return data

    def to_representation(self, instance):
        # Customize the representation if necessary
        return super().to_representation(instance)

class WorkflowCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workflow
        fields = ['name', 'json_data', 'inputs']

    def create(self, validated_data):
        # Set the user from the request context
        request = self.context.get("request", None)
        if request and hasattr(request, "user"):
            validated_data["user"] = request.user
        return super().create(validated_data)


class WorkflowJSONSerializer(serializers.Serializer):
    json_data = serializers.JSONField(help_text="The JSON data representing the workflow structure.")
