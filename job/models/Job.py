from django.db import models
from job.models.Workflow import Workflow
from user.models import User

class Job(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("running", "Running"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    workflow = models.ForeignKey(
        Workflow, on_delete=models.CASCADE
    )  # Link to the Workflow
    runtime = models.DurationField(null=True, blank=True)  # To store the runtime
    result_data = models.JSONField(
        null=True, blank=True
    )  # Store image URLs or other result data as JSON
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default="pending"
    )  # Job status
    input_data = models.JSONField(
        null=True, blank=True
    )  # Input data for the job (now JSONField)
    logs = models.TextField(null=True, blank=True)  # Field for logs
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Link to the Django user

    def __str__(self):
        return f"Job {self.id} for Workflow {self.workflow.id} - Status: {self.status}"
