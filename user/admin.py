from django.contrib import admin
from pushNotification.admin import send_notification_to_selected_users
from pushNotification.models import FCMToken
from user.models import User


class FCMTokenInline(admin.TabularInline):
    model = FCMToken
    extra = 0
    readonly_fields = ['token', 'created_at']


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['phone_number', 'full_name', 'is_active', 'role']
    search_fields = ['phone_number', 'full_name']
    list_filter = ['is_active', 'role']
    inlines = [FCMTokenInline]
    actions = [send_notification_to_selected_users]


    def get_fcm_tokens(self, obj):
        return [token.token for token in obj.get_fcm_tokens()]
