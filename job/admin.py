from django.contrib import admin
from job.models.Dataset import Character, Dataset, DatasetImage
from job.models.Job import Job
from job.models.Workflow import Workflow
from job.models.WorkflowRunner import WorkflowRunner


from django.contrib import admin
from django.utils.html import format_html
# Register your models here.
admin.site.register(Job)
admin.site.register(Workflow)
admin.site.register(WorkflowRunner)
# admin.site.register(Dataset)
# admin.site.register(DatasetImage)


from django.contrib import admin

class DatasetImageInline(admin.TabularInline):
    model = DatasetImage
    extra = 1
    readonly_fields = ['image_preview']  # Add the image preview field

    def image_preview(self, obj):
        if obj.image:
            return format_html(f'<img src="{obj.image.url}" style="width: 100px; height: auto;" />')
        return "No Image"

    image_preview.short_description = "Image Preview"

@admin.register(Dataset)
class DatasetAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_by', 'created_at']
    inlines = [DatasetImageInline]

@admin.register(Character)
class CharacterAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_by', 'created_at']
    list_filter = ['created_by']
    search_fields = ['name']
    readonly_fields = ['image_preview']

    def image_preview(self, obj):
        if obj.image:
            return format_html(f'<img src="{obj.image.url}" style="width: 100px; height: auto;" />')
        return "No Image"

    image_preview.short_description = "Image Preview"
