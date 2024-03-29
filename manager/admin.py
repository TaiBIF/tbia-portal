from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin

from .models import User, Partner, About

class CustomUserAdmin(UserAdmin):
    ...
    fieldsets =  (
        (None, {'fields': ('email', 'password', 'name', 'is_active', 'is_superuser', 'is_email_verified', 'partner_id', 'last_login','date_joined','is_staff')}),
    )
    add_fieldsets = (
        (None, {'fields': ('email', 'password', 'name', 'is_active', 'is_superuser', 'is_email_verified', 'partner_id', 'last_login','date_joined','is_staff')}),
    )
    list_filter = ()



class PartnerAdmin(admin.ModelAdmin):
    list_display = ('id', 'select_title')



admin.site.register(User, CustomUserAdmin)
admin.site.unregister(Group)
admin.site.register(Partner, PartnerAdmin)
admin.site.register(About)