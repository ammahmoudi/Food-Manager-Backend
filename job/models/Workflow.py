from django.db import models
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
            nodes.append(
                {
                    "id": node_id,
                    "name": node_info["_meta"]["title"],
                    "type": node_info["class_type"],
                }
            )
        return nodes
