from django.db import models
from user.models import User

class Dataset(models.Model):
    name = models.CharField(max_length=255)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    character = models.ForeignKey(
        "Character", 
        null=True, 
        blank=True, 
        related_name="dataset_character",  # Custom related name
        on_delete=models.SET_NULL
    )

    def __str__(self):
        return self.name

class DatasetImage(models.Model):
    dataset = models.ForeignKey(Dataset, related_name='images', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    image = models.ImageField(upload_to='dataset_images/',null=True, blank=True)  # Storing image
    complex_prompt = models.TextField(null=True, blank=True)
    tag_prompt = models.TextField(null=True, blank=True)
    negative_prompt = models.TextField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    character = models.ForeignKey(
        "Character", 
        null=True, 
        blank=True, 
        related_name="imge_character",  # Custom related name for images related to character
        on_delete=models.SET_NULL
    )

    def __str__(self):
        return self.name

class Character(models.Model):
    name = models.CharField(max_length=255)
    loras = models.JSONField(default=list, blank=True)  # List of strings representing loras
    datasets = models.ManyToManyField(
        Dataset, 
        related_name="characters",  # Custom related name for ManyToMany field
        blank=True
    )  # List of datasets
    image = models.ImageField(upload_to='characters/', null=True, blank=True)  # Character image
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
