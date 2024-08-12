from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from .models import CustomUser


class CustomUserAdmin(UserAdmin):
    """
    Custom admin panel to manage users.
    """

    # Fields displayed in the user list in admin
    list_display = ('username', 'email', 'phone', 'is_staff', 'is_active')

    # Fields by which the user list can be filtered
    list_filter = ('is_staff', 'is_active', 'date_joined')

    # Fields used for searching users
    search_fields = ('username', 'email', 'phone')

    # Fields for editing user details
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'phone', 'avatar')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )

    # Fields required when creating a user in admin
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username', 'email', 'phone', 'password1', 'password2', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'
            ),
        }),
    )

    # Fields that must be unique for each user
    ordering = ('username', 'email')
    filter_horizontal = ('groups', 'user_permissions')


# Registering the CustomUser model and admin panel
admin.site.register(CustomUser, CustomUserAdmin)

admin.site.site_header = "InnoTreyd Admin Panel"
admin.site.site_title = "InnoTreyd Admin Panel"