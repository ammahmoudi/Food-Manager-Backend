from django.contrib import admin
from django.utils.html import format_html
from job.models.Dataset import Character, Dataset, DatasetImage
from job.models.Job import Job
from job.models.Workflow import Workflow
from job.models.WorkflowRunner import WorkflowRunner


# Register Workflow and WorkflowRunner
admin.site.register(WorkflowRunner)


# Inline to show the dataset images related to a dataset
class DatasetImageInline(admin.StackedInline):
    model = DatasetImage
    extra = 1
    verbose_name = "Image"
    verbose_name_plural = "Images"
    readonly_fields = ["image_preview", "created_at"]
    fields = [
        "name", "image", "complex_prompt", "tag_prompt",
        "negative_prompt", "image_preview", "created_by",
    ]

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                f'<img src="{obj.image.url}" style="width: 150px; height: auto;" />'
            )
        return "No Image"

    image_preview.short_description = "Image Preview"


# Inline to show jobs related to a dataset
class JobInline(admin.StackedInline):
    model = Job  # Show jobs related to the dataset
    extra = 1
    verbose_name = "Job"
    verbose_name_plural = "Jobs"


# Admin for Dataset to include related jobs or images based on dataset type
@admin.register(Dataset)
class DatasetAdmin(admin.ModelAdmin):
    list_display = ["name", "created_by", "created_at", "temporary", "character", "dataset_type"]
    search_fields = ["name", "created_by__username"]
    list_filter = ["dataset_type", "temporary"]

    def get_inlines(self, request, obj=None):
        """
        Return the appropriate inlines based on the dataset type.
        If the dataset_type is 'job', it shows related jobs.
        If the dataset_type is 'image', it shows related images.
        """
        if obj and obj.dataset_type == "job":
            return [JobInline]  # Show Jobs if job-based
        return [DatasetImageInline]  # Show Images if image-based

    def get_queryset(self, request):
        """
        Customize queryset to optimize for admin performance.
        """
        qs = super().get_queryset(request)
        return qs.select_related("character", "created_by")


# Admin for DatasetImage to show image details in list view
@admin.register(DatasetImage)
class DatasetImageAdmin(admin.ModelAdmin):
    list_display = ["name", "image_preview", "complex_prompt", "tag_prompt", "negative_prompt", "created_by", "created_at"]
    search_fields = ["name", "created_by__username", "complex_prompt", "tag_prompt", "negative_prompt"]
    readonly_fields = ["image_preview"]

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                f'<img src="{obj.image.url}" style="width: 100px; height: auto;" />'
            )
        return "No Image"

    image_preview.short_description = "Image Preview"


# Admin for Workflow to show relevant data in list view
@admin.register(Workflow)
class WorkflowAdmin(admin.ModelAdmin):
    list_display = ["name", "user", "last_modified", "input_count", "output_count"]
    search_fields = ["name", "user__username"]
    list_filter = ["last_modified"]

    def input_count(self, obj):
        """Display the number of inputs."""
        return len(obj.inputs)

    input_count.short_description = "Number of Inputs"

    def output_count(self, obj):
        """Display the number of outputs."""
        return len(obj.outputs)

    output_count.short_description = "Number of Outputs"

    def get_queryset(self, request):
        """
        Customize queryset to optimize for admin performance.
        """
        qs = super().get_queryset(request)
        return qs.select_related("user")

# Admin for Character model
@admin.register(Character)
class CharacterAdmin(admin.ModelAdmin):
    list_display = ["name", "created_by", "created_at"]
    list_filter = ["created_by"]
    search_fields = ["name"]
    readonly_fields = ["image_preview"]

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                f'<img src="{obj.image.url}" style="width: 100px; height: auto;" />'
            )
        return "No Image"

    image_preview.short_description = "Image Preview"
@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ['id', 'workflow', 'status', 'user', 'runtime', 'dataset']
    search_fields = ['workflow__name', 'user__username']
    list_filter = ['status', 'dataset']

    def dataset(self, obj):
        """Show the dataset associated with the job."""
        return obj.datasets.first().name if obj.datasets.exists() else "No Dataset"

    dataset.short_description = "Dataset"
