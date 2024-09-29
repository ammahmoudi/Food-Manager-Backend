from django.db import models
from django.forms import JSONField

from user.models import User


class Workflow(models.Model):
    name = models.CharField(max_length=500)
    json_data = models.JSONField()  # Stores the workflow JSON data as a JSONField
    last_modified = models.DateTimeField(auto_now=True)  # Automatically set on update
    inputs = models.JSONField()  # Stores input mapping like {node_id: input_name}
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Link to the Django user

    def __str__(self):
        return f"Workflow {self.id}"

    def parse_nodes(self):
        nodes = []
        for node_id, node_info in self.json_data.items():
            nodes.append({
                'id': node_id,
                'name': node_info['_meta']['title'],
                'type': node_info['class_type'],
            })
        return nodes

class Job(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE)  # Link to the Workflow
    runtime = models.DurationField(null=True, blank=True)  # To store the runtime
    result_data = models.JSONField(null=True, blank=True)  # Store image URLs or other result data as JSON
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')  # Job status
    input_data = models.JSONField(null=True, blank=True)  # Input data for the job (now JSONField)
    logs = models.TextField(null=True, blank=True)  # Field for logs
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Link to the Django user

    def __str__(self):
        return f"Job {self.id} for Workflow {self.workflow.id} - Status: {self.status}"
class SpecializedWorkflowRunner(models.Model):
    workflow = models.ForeignKey('Workflow', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    input_mapping = JSONField(help_text="Mapping of API inputs to workflow inputs")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name