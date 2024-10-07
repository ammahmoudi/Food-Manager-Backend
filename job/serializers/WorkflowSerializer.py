from rest_framework import serializers
from job.models.Workflow import Workflow


class WorkflowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workflow
        fields = ["id", "name", "json_data", "last_modified", "inputs", "outputs", "user"]

    def to_representation(self, instance):
        # Get the original representation (default serialization)
        representation = super().to_representation(instance)

        # Extract nodes from the json_data
        nodes = self.extract_nodes_from_json(instance.json_data)

        # Modify inputs to include node names and structure inputs
        modified_inputs = {}
        for node_id, input_data in representation['inputs'].items():
            # Find the corresponding node by ID
            node = next((node for node in nodes if node["id"] == node_id), None)
            if node:
                node_name = node["name"]
                # Structure inputs: add node name and structured input data
                modified_inputs[node_id] = {
                    "name": node_name,
                    "inputs": input_data  # Add the existing input types
                }
            else:
                # If node is not found, structure with unknown name
                modified_inputs[node_id] = {
                    "name": "Unknown",
                    "inputs": input_data
                }

        # Modify outputs to include node names and structure outputs
        modified_outputs = {}
        for node_id, output_data in representation['outputs'].items():
            # Find the corresponding node by ID
            node = next((node for node in nodes if node["id"] == node_id), None)
            if node:
                node_name = node["name"]
                # Structure outputs: add node name and structured output data
                modified_outputs[node_id] = {
                    "name": node_name,
                    "outputs": output_data  # Add the existing output types
                }
            else:
                # If node is not found, structure with unknown name
                modified_outputs[node_id] = {
                    "name": "Unknown",
                    "outputs": output_data
                }

        # Replace the inputs and outputs in the representation with the structured versions
        representation['inputs'] = modified_inputs
        representation['outputs'] = modified_outputs

        return representation

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
                "outputs": (
                    list(node_info["outputs"].keys()) if "outputs" in node_info else []
                ),
            }
            nodes.append(node)
        return nodes



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
        fields = ["name", "json_data", "inputs","outputs"]

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
