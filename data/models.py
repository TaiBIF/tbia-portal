from django.db import models
from django.utils import timezone


# deprecated - 移至datahub
# 新舊TaiCOL namecode對應 & TaiEOL對應
# class Namecode(models.Model): 
#     taxon_name_id = models.CharField(max_length=100, blank=False, null=False)
#     namecode = models.CharField(max_length=100, blank=False, null=False)
#     taieol_id = models.CharField(max_length=100, blank=True, null=True)


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
        # indexes = [
        #     models.UniqueIndex(fields=['name','record_type','group'], name='dataset_idx'),
        # ]
        constraints = [
            models.UniqueConstraint(fields=['taxonID','taxon_name_id'], name='taxonID_taxon_name_id_unique')
        ]

# for get_variants 異體字
class Variant(models.Model):
    char = models.CharField(blank=True, null=True, max_length=10)
    pattern = models.CharField(blank=True, null=True, max_length=1000)
    char_len = models.IntegerField(default=1)



# deprecated - 移至solr
# class Taxon(models.Model):
#     taxonID = models.CharField(max_length=20, blank=True, null=True)
#     name_status = models.CharField(max_length=20, blank=True, null=True)
#     aberration = models.CharField(blank=True, null=True, max_length=10000)
#     aberration_c = models.CharField(blank=True, null=True, max_length=10000)
#     alternative_name_c = models.CharField(blank=True, null=True, max_length=10000)
#     vars()['class'] = models.CharField(blank=True, null=True, max_length=10000)
#     class_c = models.CharField(blank=True, null=True, max_length=10000)
#     common_name_c = models.CharField(blank=True, null=True, max_length=10000)
#     division = models.CharField(blank=True, null=True, max_length=10000)
#     division_c = models.CharField(blank=True, null=True, max_length=10000)
#     domain = models.CharField(blank=True, null=True, max_length=10000)
#     domain_c = models.CharField(blank=True, null=True, max_length=10000)
#     family = models.CharField(blank=True, null=True, max_length=10000)
#     family_c = models.CharField(blank=True, null=True, max_length=10000)
#     formatted_genus = models.CharField(blank=True, null=True, max_length=10000)
#     formatted_subgenus = models.CharField(blank=True, null=True, max_length=10000)
#     formatted_section = models.CharField(blank=True, null=True, max_length=10000)
#     formatted_subsection = models.CharField(blank=True, null=True, max_length=10000)
#     formatted_species = models.CharField(blank=True, null=True, max_length=10000)
#     formatted_subspecies = models.CharField(blank=True, null=True, max_length=10000)
#     formatted_nothosubspecies = models.CharField(blank=True, null=True, max_length=10000)
#     formatted_variety = models.CharField(blank=True, null=True, max_length=10000)
#     formatted_subvariety = models.CharField(blank=True, null=True, max_length=10000)
#     formatted_nothovariety = models.CharField(blank=True, null=True, max_length=10000)
#     formatted_form = models.CharField(blank=True, null=True, max_length=10000)
#     formatted_subform = models.CharField(blank=True, null=True, max_length=10000)
#     formatted_specialform = models.CharField(blank=True, null=True, max_length=10000)
#     formatted_race = models.CharField(blank=True, null=True, max_length=10000)
#     formatted_strip = models.CharField(blank=True, null=True, max_length=10000)
#     formatted_morph = models.CharField(blank=True, null=True, max_length=10000)
#     formatted_aberration = models.CharField(blank=True, null=True, max_length=10000)
#     formatted_hybridformula = models.CharField(blank=True, null=True, max_length=10000)
#     formatted_name = models.CharField(blank=True, null=True, max_length=10000)
#     formatted_synonyms = models.CharField(blank=True, null=True, max_length=10000)
#     formatted_misapplied = models.CharField(blank=True, null=True, max_length=10000)
#     form = models.CharField(blank=True, null=True, max_length=10000)
#     form_c = models.CharField(blank=True, null=True, max_length=10000)
#     genus = models.CharField(blank=True, null=True, max_length=10000)
#     genus_c = models.CharField(blank=True, null=True, max_length=10000)
#     hybridformula = models.CharField(blank=True, null=True, max_length=10000)
#     hybridformula_c = models.CharField(blank=True, null=True, max_length=10000)
#     infraclass = models.CharField(blank=True, null=True, max_length=10000)
#     infraclass_c = models.CharField(blank=True, null=True, max_length=10000)
#     infradivision = models.CharField(blank=True, null=True, max_length=10000)
#     infradivision_c = models.CharField(blank=True, null=True, max_length=10000)
#     infrakingdom = models.CharField(blank=True, null=True, max_length=10000)
#     infrakingdom_c = models.CharField(blank=True, null=True, max_length=10000)
#     infraorder = models.CharField(blank=True, null=True, max_length=10000)
#     infraorder_c = models.CharField(blank=True, null=True, max_length=10000)
#     infraphylum = models.CharField(blank=True, null=True, max_length=10000)
#     infraphylum_c = models.CharField(blank=True, null=True, max_length=10000)
#     kingdom = models.CharField(blank=True, null=True, max_length=10000)
#     kingdom_c = models.CharField(blank=True, null=True, max_length=10000)
#     microphylum = models.CharField(blank=True, null=True, max_length=10000)
#     microphylum_c = models.CharField(blank=True, null=True, max_length=10000)
#     misapplied = models.CharField(blank=True, null=True, max_length=10000)
#     morph = models.CharField(blank=True, null=True, max_length=10000)
#     morph_c = models.CharField(blank=True, null=True, max_length=10000)
#     name_author = models.CharField(blank=True, null=True, max_length=10000)
#     nothosubspecies = models.CharField(blank=True, null=True, max_length=10000)
#     nothosubspecies_c = models.CharField(blank=True, null=True, max_length=10000)
#     nothovariety = models.CharField(blank=True, null=True, max_length=10000)
#     nothovariety_c = models.CharField(blank=True, null=True, max_length=10000)
#     order = models.CharField(blank=True, null=True, max_length=10000)
#     order_c = models.CharField(blank=True, null=True, max_length=10000)
#     parvdivision = models.CharField(blank=True, null=True, max_length=10000)
#     parvdivision_c = models.CharField(blank=True, null=True, max_length=10000)
#     parvphylum = models.CharField(blank=True, null=True, max_length=10000)
#     parvphylum_c = models.CharField(blank=True, null=True, max_length=10000)
#     phylum = models.CharField(blank=True, null=True, max_length=10000)
#     phylum_c = models.CharField(blank=True, null=True, max_length=10000)
#     race = models.CharField(blank=True, null=True, max_length=10000)
#     race_c = models.CharField(blank=True, null=True, max_length=10000)
#     scientificName = models.CharField(blank=True, null=True, max_length=10000)
#     scientificNameID = models.CharField(blank=True, null=True, max_length=10000)
#     section = models.CharField(blank=True, null=True, max_length=10000)
#     section_c = models.CharField(blank=True, null=True, max_length=10000)
#     specialform = models.CharField(blank=True, null=True, max_length=10000)
#     specialform_c = models.CharField(blank=True, null=True, max_length=10000)
#     species = models.CharField(blank=True, null=True, max_length=10000)
#     species_c = models.CharField(blank=True, null=True, max_length=10000)
#     stirp = models.CharField(blank=True, null=True, max_length=10000)
#     stirp_c = models.CharField(blank=True, null=True, max_length=10000)
#     subclass = models.CharField(blank=True, null=True, max_length=10000)
#     subclass_c = models.CharField(blank=True, null=True, max_length=10000)
#     subdivision = models.CharField(blank=True, null=True, max_length=10000)
#     subdivision_c = models.CharField(blank=True, null=True, max_length=10000)
#     subfamily = models.CharField(blank=True, null=True, max_length=10000)
#     subfamily_c = models.CharField(blank=True, null=True, max_length=10000)
#     subform = models.CharField(blank=True, null=True, max_length=10000)
#     subform_c = models.CharField(blank=True, null=True, max_length=10000)
#     subgenus = models.CharField(blank=True, null=True, max_length=10000)
#     subgenus_c = models.CharField(blank=True, null=True, max_length=10000)
#     subkingdom = models.CharField(blank=True, null=True, max_length=10000)
#     subkingdom_c = models.CharField(blank=True, null=True, max_length=10000)
#     suborder = models.CharField(blank=True, null=True, max_length=10000)
#     suborder_c = models.CharField(blank=True, null=True, max_length=10000)
#     subphylum = models.CharField(blank=True, null=True, max_length=10000)
#     subphylum_c = models.CharField(blank=True, null=True, max_length=10000)
#     subsection = models.CharField(blank=True, null=True, max_length=10000)
#     subsection_c = models.CharField(blank=True, null=True, max_length=10000)
#     subspecies = models.CharField(blank=True, null=True, max_length=10000)
#     subspecies_c = models.CharField(blank=True, null=True, max_length=10000)
#     subtribe = models.CharField(blank=True, null=True, max_length=10000)
#     subtribe_c = models.CharField(blank=True, null=True, max_length=10000)
#     subvariety = models.CharField(blank=True, null=True, max_length=10000)
#     subvariety_c = models.CharField(blank=True, null=True, max_length=10000)
#     superclass = models.CharField(blank=True, null=True, max_length=10000)
#     superclass_c = models.CharField(blank=True, null=True, max_length=10000)
#     superdivision = models.CharField(blank=True, null=True, max_length=10000)
#     superdivision_c = models.CharField(blank=True, null=True, max_length=10000)
#     superfamily = models.CharField(blank=True, null=True, max_length=10000)
#     superfamily_c = models.CharField(blank=True, null=True, max_length=10000)
#     superkingdom = models.CharField(blank=True, null=True, max_length=10000)
#     superkingdom_c = models.CharField(blank=True, null=True, max_length=10000)
#     superorder = models.CharField(blank=True, null=True, max_length=10000)
#     superorder_c = models.CharField(blank=True, null=True, max_length=10000)
#     superphylum = models.CharField(blank=True, null=True, max_length=10000)
#     superphylum_c = models.CharField(blank=True, null=True, max_length=10000)
#     synonyms = models.CharField(blank=True, null=True, max_length=10000)
#     taxonRank = models.CharField(blank=True, null=True, max_length=10000)
#     tribe = models.CharField(blank=True, null=True, max_length=10000)
#     tribe_c = models.CharField(blank=True, null=True, max_length=10000)
#     variety = models.CharField(blank=True, null=True, max_length=10000)
#     variety_c = models.CharField(blank=True, null=True, max_length=10000)
#     cites = models.CharField(blank=True, null=True, max_length=100)
#     iucn = models.CharField(blank=True, null=True, max_length=100)
#     redlist = models.CharField(blank=True, null=True, max_length=100)
#     protected = models.CharField(blank=True, null=True, max_length=100)
#     sensitive = models.CharField(blank=True, null=True, max_length=100)
#     alien_type = models.CharField(blank=True, null=True, max_length=10000)
#     is_endemic = models.BooleanField(blank=True, null=True) 
#     is_fossil = models.BooleanField(blank=True, null=True) 
#     is_terrestrial = models.BooleanField(blank=True, null=True) 
#     is_freshwater = models.BooleanField(blank=True, null=True) 
#     is_brackish = models.BooleanField(blank=True, null=True) 
#     is_marine = models.BooleanField(blank=True, null=True) 

# deprecated - 移至datahub
# class DatasetKey(models.Model):
#     name = models.CharField(max_length=1000, blank=False, null=False, db_index=True)
#     record_type = models.CharField(max_length=20, blank=False, null=False, db_index=True)
#     rights_holder = models.CharField(max_length=100, blank=True, null=True, db_index=True) # 來源資料庫
#     deprecated = models.BooleanField(default=False) # 資料庫內是否還有此資料集名稱

#     class Meta:
#         # indexes = [
#         #     models.UniqueIndex(fields=['name','record_type','group'], name='dataset_idx'),
#         # ]
#         constraints = [
#             models.UniqueConstraint(fields=['name','record_type','rights_holder'], name='dataset_unique')
#         ]