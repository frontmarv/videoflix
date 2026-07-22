from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Admin interface for CustomUser model.

    Customizes Django admin to work with email-based authentication instead
    of the default username field. Displays user status, permissions, and
    important dates for account management.
    """
    model = CustomUser
    list_display = ['email', 'username',
                    'is_activated', 'is_staff', 'is_active']
    list_filter = ['is_activated', 'is_staff', 'is_active']
    search_fields = ['email', 'username']
    ordering = ['email']
    readonly_fields = ['date_joined', 'last_login']
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('username',)}),
        ('Permissions', {'fields': ('is_activated', 'is_active', 'is_staff',
         'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'is_activated'),
        }),
    )
