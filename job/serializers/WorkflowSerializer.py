from rest_framework import serializers
from job.models.Workflow import Workflow


class WorkflowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workflow
        fields = ["id", "name", "json_data", "last_modified", "inputs", "user"]


class NodeInputSerializer(serializers.Serializer):
    """Handles both string and file types for node inputs."""

    input_value = serializers.CharField(required=False)
    input_file = serializers.ImageField(required=False)

    def to_internal_value(self, data):
        if isinstance(data, str):
            return {"input_value": data}  # Handle string input
        elif hasattr(data, "read"):  # Check if it's a file object
            return {"input_file": data}  # Handle image file
        raise serializers.ValidationError(
            "Each input must be a string or an image file."
        )


class RunWorkflowSerializer(serializers.Serializer):
    """Serializer to handle workflow inputs with nodes."""

    inputs = serializers.DictField(
        child=serializers.DictField(
            child=NodeInputSerializer(),
            help_text="Each node input may contain either a string or an image file.",
        ),
        help_text="A dictionary of node IDs and their input data (either a string or an image file).",
    )


class WorkflowCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workflow
        fields = ["name", "json_data", "inputs"]

    def create(self, validated_data):
        # Set the user from the request context
        request = self.context.get("request", None)
        if request and hasattr(request, "user"):
            validated_data["user"] = request.user
        return super().create(validated_data)


class WorkflowJSONSerializer(serializers.Serializer):
    json_data = serializers.JSONField(
        help_text="The JSON data representing the workflow structure."
    )
