from django.db import models

# Create your models here.

''''
CharField is generally used for storing small strings like first name, last name, etc. To store larger text TextField is used.
max_length is required for CharField
'''

# TaiCoL taxon-based
class Taixon(models.Model):
    taxonUUID = models.CharField(max_length=1000, unique=True)
    name_id = models.CharField(max_length=1000)
    simple_name = models.TextField()
    name_author = models.TextField()
    synonyms = models.TextField()
    misapplied = models.TextField()
    rank = models.CharField(max_length=100)
    common_name_c = models.CharField()
    alternative_name_c = models.TextField()
    taxon_created = models.DateField()
    usage_modified = models.DateField()
    Domain = models.CharField(max_length=100)
    Superkingdom = models.CharField(max_length=100)
    Kingdom = models.CharField(max_length=100)
    Subkingdom = models.CharField(max_length=100)
    Infrakingdom = models.CharField(max_length=100)
    Superdivision = models.CharField(max_length=100)
    Division = models.CharField(max_length=100)
    Subdivision = models.CharField(max_length=100)
    Infradivision = models.CharField(max_length=100)
    Parvdivision = models.CharField(max_length=100)
    Superphylum = models.CharField(max_length=100)
    Phylum = models.CharField(max_length=100)
    Subphylum = models.CharField(max_length=100)
    Infraphylum = models.CharField(max_length=100)
    Microphylum = models.CharField(max_length=100)
    Parvphylum = models.CharField(max_length=100)
    Superclass = models.CharField(max_length=100)
    Class = models.CharField(max_length=100)
    Subclass = models.CharField(max_length=100)
    Infraclass = models.CharField(max_length=100)
    Superorder = models.CharField(max_length=100)
    Order = models.CharField(max_length=100)
    Suborder = models.CharField(max_length=100)
    Infraorder = models.CharField(max_length=100)
    Superfamily = models.CharField(max_length=100)
    Family = models.CharField(max_length=100)
    Subfamily = models.CharField(max_length=100)
    Tribe = models.CharField(max_length=100)
    Subtribe = models.CharField(max_length=100)
    Genus = models.CharField(max_length=100)
    Subgenus = models.CharField(max_length=100)
    Section = models.CharField(max_length=100)
    Subsection = models.CharField(max_length=100)
    Species = models.CharField(max_length=100)
    # Subspecies = models.CharField(max_length=100)
    # Nothosubspecies = models.CharField(max_length=100)
    # Variety = models.CharField(max_length=100)
    # Subvariety = models.CharField(max_length=100)
    # Nothovariety = models.CharField(max_length=100)
    # Form = models.CharField(max_length=100)
    # Subform = models.CharField(max_length=100)
    # SpecialForm = models.CharField(max_length=100)
    # Race = models.CharField(max_length=100)
    # Stirp = models.CharField(max_length=100)
    # Morph = models.CharField(max_length=100)
    # Aberration = models.CharField(max_length=100)
    # HybridFormula = models.CharField(max_length=100)
    created = models.DateField(auto_now_add=True)
    modified = models.DateField(auto_now_add=True)

# 物種出現紀錄
class Occurrence(models.Model):
    def tbiaUUID(self):
       return f'occ{self.id}'

# 自然史典藏
class Collection(models.Model):
    def tbiaUUID(self):
       return f'col{self.id}'

