from rest_framework import serializers

from job.models.WorkflowRunner import WorkflowRunner

class WorkflowRunnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowRunner
        fields = ['id', 'workflow', 'name', 'input_mapping', 'created_by', 'created_at']
