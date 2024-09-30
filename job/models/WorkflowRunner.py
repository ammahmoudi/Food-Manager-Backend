from django.db import models
from user.models import User

class WorkflowRunner(models.Model):
    workflow = models.ForeignKey("Workflow", on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    input_mapping = models.JSONField(default=dict)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
