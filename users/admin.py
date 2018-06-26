from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import ugettext_lazy as _
from .models.user import User


class UserAdmin(UserAdmin):
    list_display = ['id', 'phone', 'verified', 'verified_ts']
    readonly_fields = ['date_joined', 'last_login', 'verified_ts', 'updated']
    fieldsets = [
        (None, {
            'fields': ['username', 'password']
        }),
        (_('Personal info'), {
            'fields': ['first_name', 'last_name', 'phone', 'email']
        }),
        (_('Account state'), {
            'fields': ['is_active', 'verified']
        }),
        (_('Permissions'), {
            'classes': ['collapse'],
            'fields': ['is_staff', 'is_superuser', 'groups', 'user_permissions']
        }),
        (_('Important dates'), {
            'fields': ['last_login', 'date_joined', 'verified_ts', 'updated']
        }),
    ]
    add_fieldsets = [
        (None, {'classes': ['wide', ],
                'fields': ['username', 'phone', 'password1', 'password2']})
    ]

admin.site.register(User, UserAdmin)
