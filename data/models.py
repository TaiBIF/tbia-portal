from django.db import models
from django.utils import timezone

# 新舊TaiCOL namecode對應
class Namecode(models.Model): 
    taxon_name_id = models.CharField(max_length=100, blank=False, null=False)
    namecode = models.CharField(max_length=100, blank=False, null=False)


