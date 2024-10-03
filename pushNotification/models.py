from django.db import models

from user.models import User

class FCMToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="fcm_tokens")
    token = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.token

class PushNotification(models.Model):
    title = models.CharField(max_length=255, null=True, blank=True)
    message = models.TextField()
    image_url = models.URLField(null=True, blank=True)
    link = models.URLField(null=True, blank=True)
    sent_time = models.DateTimeField(auto_now_add=True)
    sent_tokens = models.ManyToManyField(FCMToken, related_name="push_notifications")

    def __str__(self):
        return self.message[:50]
