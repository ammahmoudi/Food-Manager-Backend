from django.contrib import admin
from django.shortcuts import render
from pushNotification.models import FCMToken, PushNotification

from django import forms
from django.http import HttpResponseRedirect
from utils.firebase import send_push_notification
import os

from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
admin.site.register(FCMToken)
admin.site.register(PushNotification)
# Form for admin to input notification details
class PushNotificationAdminForm(forms.Form):
    selected_action = forms.CharField(widget=forms.MultipleHiddenInput)  # Rename the field to avoid underscore
    title = forms.CharField(max_length=255, label="Notification Title")
    message = forms.CharField(widget=forms.Textarea, label="Notification Body")
    link = forms.URLField(required=False, label="Notification Link (Optional)")
    image = forms.ImageField(required=False, label="Notification Image (Optional)")
# Admin action to send notification to selected users
@admin.action(description="Send notification to selected users")
def send_notification_to_selected_users(modeladmin, request, queryset):
    # If the form is submitted, process it
    if 'apply' in request.POST:
        form = PushNotificationAdminForm(request.POST, request.FILES)
        if form.is_valid():
            title = form.cleaned_data['title']
            message = form.cleaned_data['message']
            link = form.cleaned_data['link']
            image = form.cleaned_data.get('image')

            # Create a new notification entry
            notification = PushNotification.objects.create(
                title=title, message=message, link=link
            )

            # Handle image saving if provided
            if image:
                image_name = urlsafe_base64_encode(force_bytes(image.name)) + '.png'
                image_path = os.path.join("push_notifications", image_name)
                full_image_path = default_storage.save(
                    image_path, ContentFile(image.read())
                )
                # Store the full URL of the image
                notification.image_url = request.build_absolute_uri(
                    default_storage.url(full_image_path)
                )
                notification.save()

            # Send notifications to selected users
            for user in queryset:
                tokens = user.get_fcm_tokens()
                for token in tokens:
                    try:
                        send_push_notification(token.token, title, message, notification.image_url, link)
                        token_obj = FCMToken.objects.get(token=token.token)
                        notification.sent_tokens.add(token_obj)
                    except Exception as e:
                        print(f"Error sending notification to {token}: {e}")

            # Save notification and display success message
            notification.save()
            modeladmin.message_user(request, f"Notification sent to {queryset.count()} users.")
            return HttpResponseRedirect(request.get_full_path())

    else:
        selected_action = request.POST.getlist(admin.helpers.ACTION_CHECKBOX_NAME)
        form = PushNotificationAdminForm(initial={'selected_action': selected_action})
        return render(request, 'admin/send_notification_form.html', {'form': form, 'users': queryset})
