from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *

# Register your models here.
admin.site.register(News)
admin.site.register(Resource)
admin.site.register(Feedback)
admin.site.register(Notification)
admin.site.register(Download)