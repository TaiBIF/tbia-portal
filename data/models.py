from django.db import models


# for higherTaxa autocomplete
class Name(models.Model):
    # 自己的name? 接受的name?
    name = models.CharField(blank=True, null=True, max_length=10000)
    accepted_name = models.CharField(blank=True, null=True, max_length=10000)
    # name_author = models.CharField(blank=True, null=True, max_length=10000)
    accepted_common_name_c = models.CharField(blank=True, null=True, max_length=10000)
    accepted_alternative_name_c = models.CharField(blank=True, null=True, max_length=10000)
    name_status = models.CharField(blank=True, null=True, max_length=20)
    taxonID = models.CharField(blank=True, null=True, max_length=20)
    taxon_name_id = models.IntegerField(blank=True, null=True)
    modified = models.DateTimeField(null=True, blank=True, auto_now=True)
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['taxonID','taxon_name_id'], name='taxonID_taxon_name_id_unique')
        ]

# for get_variants 異體字
class Variant(models.Model):
    char = models.CharField(blank=True, null=True, max_length=10)
    pattern = models.CharField(blank=True, null=True, max_length=1000)
    char_len = models.IntegerField(default=1)
