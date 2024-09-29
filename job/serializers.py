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

        # Ensure result_data exists and is not None
        result_data = representation.get('result_data', None)
        if result_data and 'image_urls' in result_data:
            image_urls = result_data['image_urls']
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





class NodeInputSerializer(serializers.Serializer):
    """Handles both string and file types for node inputs."""
    input_value = serializers.CharField(required=False)
    input_file = serializers.ImageField(required=False)

    def to_internal_value(self, data):
        if isinstance(data, str):
            return {"input_value": data}  # Handle string input
        elif hasattr(data, "read"):  # Check if it's a file object
            return {"input_file": data}  # Handle image file
        raise serializers.ValidationError("Each input must be a string or an image file.")

class RunWorkflowSerializer(serializers.Serializer):
    """Serializer to handle workflow inputs with nodes."""
    inputs = serializers.DictField(
        child=serializers.DictField(
            child=NodeInputSerializer(),
            help_text="Each node input may contain either a string or an image file."
        ),
        help_text="A dictionary of node IDs and their input data (either a string or an image file)."
    )








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
from rest_framework import serializers
from .models import SpecializedWorkflowRunner

class SpecializedWorkflowRunnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpecializedWorkflowRunner
        fields = ['id', 'workflow', 'name', 'input_mapping', 'created_by', 'created_at']
