from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin

from .models import User, Partner

class CustomUserAdmin(UserAdmin):
    ...
    fieldsets =  (
        (None, {'fields': ('username', 'password', 'first_name', 'last_name', 'is_active', 'is_superuser', 'is_email_verified', 'partner', 'role', 'last_login','date_joined','is_staff')}),
    )
    add_fieldsets = (
        (None, {'fields': ('username', 'password', 'first_name', 'last_name', 'is_active', 'is_superuser', 'is_email_verified', 'partner', 'role', 'last_login','date_joined','is_staff')}),
    )
    list_filter = ()



admin.site.register(User, CustomUserAdmin)
admin.site.unregister(Group)
admin.site.register(Partner)