from django.contrib import admin

from job.models import Job, Workflow

# Register your models here.
admin.site.register(Job)
admin.site.register(Workflow)
