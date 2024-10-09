import json
from rest_framework import serializers
from urllib.parse import urljoin

from job.models.Job import Job

class JobSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = ['id', 'workflow', 'status', 'runtime', 'images', 'result_data', 'input_data', 'logs', 'user', 'dataset']

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        # Get the request object from context
        request = self.context.get('request')

        # Ensure result_data exists and is not None
        result_data = representation.get('result_data', None)
        if result_data:
            # Traverse through result_data and update image URLs
            for node_id, outputs in result_data.items():
                for input_name, output in outputs.items():
                    if output.get('type') == 'image':
                        # Convert relative URL to full URL
                        image_url = output.get('value', '')
                        if image_url and request:
                            if not image_url.startswith('http'):
                                full_url = urljoin(request.build_absolute_uri('/'), image_url.lstrip('/'))
                                representation['result_data'][node_id][input_name]['value'] = full_url

        # Handle extra_images in logs
        logs = representation.get('logs', None)
        if logs and request:
            try:
                # Attempt to parse logs as JSON
                logs_data = json.loads(logs)
                extra_images = logs_data.get('extra_images', [])
                
                for image_entry in extra_images:
                    image_url = image_entry.get('image_url', '')
                    if image_url and not image_url.startswith('http'):
                        full_url = urljoin(request.build_absolute_uri('/'), image_url.lstrip('/'))
                        image_entry['image_url'] = full_url

                # Re-serialize logs back to string after updating image URLs
                representation['logs'] = json.dumps(logs_data)
            except json.JSONDecodeError:
                # In case logs are not in valid JSON format, keep them as is
                pass

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
