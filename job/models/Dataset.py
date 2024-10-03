from django.db import models
from job.models.Job import Job
from user.models import User
from django.db import models
from user.models import User


class Dataset(models.Model):
    DATASET_TYPE_CHOICES = (
        ("image", "Image Dataset"),
        ("job", "Job Dataset"),
    )
    name = models.CharField(max_length=255)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    character = models.ForeignKey(
        "Character",
        null=True,
        blank=True,
        related_name="dataset_character",
        on_delete=models.SET_NULL,
    )
    temporary = models.BooleanField(default=False)  # Temporary datasets
    dataset_type = models.CharField(
        max_length=10, choices=DATASET_TYPE_CHOICES, default="job"
    )  # New field to differentiate

    def __str__(self):
        return self.name
    @property
    def is_job_based(self):
        """Return True if the dataset type is 'job'."""
        return self.dataset_type == "job"

    def get_images(self):
        """
        Return all images associated with this dataset, whether through jobs or directly.
        - If the dataset is job-based, return images from jobs related to this dataset.
        - If the dataset is image-based, return the images directly associated with this dataset.
        """
        if self.is_job_based:
            # Return all images associated with jobs in this dataset
            return DatasetImage.objects.filter(job__dataset=self)
        else:
            # Return all images directly associated with this dataset
            return self.images.all()


class DatasetImage(models.Model):
    name = models.CharField(max_length=255)
    image = models.ImageField(upload_to="dataset_images/", null=True, blank=True)
    job = models.ForeignKey(
        "Job", related_name="images", null=True, blank=True, on_delete=models.SET_NULL
    )
    dataset = models.ForeignKey(
        "Dataset",
        related_name="images",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    complex_prompt = models.TextField(null=True, blank=True)
    tag_prompt = models.TextField(null=True, blank=True)
    negative_prompt = models.TextField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    character = models.ForeignKey(
        "Character",
        null=True,
        blank=True,
        related_name="imge_character",
        on_delete=models.SET_NULL,
    )

    def __str__(self):
        return self.name

    def get_full_image_url(self, request):
        """Returns the full URL for the image."""
        if self.image:
            return request.build_absolute_uri(self.image.url)
        return None


class Character(models.Model):
    name = models.CharField(max_length=255)
    loras = models.JSONField(
        default=dict, blank=True
    )  # List of strings representing loras
    datasets = models.ManyToManyField(
        Dataset,
        related_name="characters",  # Custom related name for ManyToMany field
        blank=True,
    )  # List of datasets
    image = models.ImageField(
        upload_to="characters/", null=True, blank=True
    )  # Character image
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
