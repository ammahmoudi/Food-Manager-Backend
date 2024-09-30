from django.contrib import admin
from job.models.Job import Job
from job.models.Workflow import Workflow
from job.models.WorkflowRunner import WorkflowRunner

# Register your models here.
admin.site.register(Job)
admin.site.register(Workflow)
admin.site.register(WorkflowRunner)
