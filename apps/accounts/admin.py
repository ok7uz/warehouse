from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from .models import CustomUser


class CustomUserAdmin(UserAdmin):
    """
    Custom admin panel to manage users.
    """

    list_display = ('username', 'email', 'phone', 'is_staff', 'is_active', 'related_users_list')

    list_filter = ('is_staff', 'is_active', 'date_joined')

    search_fields = ('username', 'email', 'phone')

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'phone', 'avatar')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username', 'email', 'phone', 'password1', 'password2', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'
            ),
        }),
    )

    filter_horizontal = ('groups', 'user_permissions')
    ordering = ('username', 'email')

    def related_users_list(self, obj):
        # Assuming the related users are stored in a ManyToManyField in CustomUser
        return ", ".join([user.username for user in obj.author_user.all()])

    related_users_list.short_description = "Related Users"

admin.site.register(CustomUser, CustomUserAdmin)

admin.site.site_header = "InnoTreid Admin Panel"
admin.site.site_title = "InnoTreid Admin Panel"