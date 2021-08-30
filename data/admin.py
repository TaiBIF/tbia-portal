from django.contrib import admin
from .models import *
# Register your models here.

admin.site.register(Taxon)
admin.site.register(Collection)
admin.site.register(Occurrence)