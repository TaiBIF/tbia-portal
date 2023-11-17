from conf.settings import env

SOLR_PREFIX = env('SOLR_PREFIX')

occ_fields = ['scientificName', 'common_name_c', 'alternative_name_c', 'synonyms', 'misapplied', 'sourceScientificName', 
              'sourceVernacularName', 'originalScientificName', 'taxonRank', 'kingdom', 'phylum', 'class', 'order', 
              'family', 'genus', 'species', 'kingdom_c', 'phylum_c', 'class_c', 'order_c', 'family_c', 'genus_c', 
              'rightsHolder', 'sensitiveCategory', 'locality', 'recordedBy', 'basisOfRecord', 'datasetName', 'license', 'eventDate']


occ_facets = {}
occ_facets['facet'] = {}

for f in occ_fields:
    occ_facets['facet'][f] = {
        'type': 'terms',
        'field': f,
        'mincount': 1,
        'limit': 30,
        'allBuckets': True,
        'numBuckets': True,
        'facet':{
            'taxonID':{
                'type': 'terms',
                'field': 'taxonID',
                'limit': 30,
                'numBuckets': True,
            },
        } 
    }


col_fields = ['scientificName', 'common_name_c', 'alternative_name_c', 'synonyms', 'misapplied', 'sourceScientificName', 
              'sourceVernacularName', 'originalScientificName', 'rightsHolder', 'sensitiveCategory', 'taxonRank', 
              'locality', 'recordedBy', 'typeStatus', 'preservation', 'datasetName', 'license', 'kingdom', 'phylum', 
              'class', 'order', 'family', 'genus', 'species', 'kingdom_c', 'phylum_c', 'class_c', 'order_c', 'family_c', 'genus_c', 'eventDate']

col_facets = {}
col_facets['facet'] = {}

for f in col_fields:
    col_facets['facet'][f] = {
        'type': 'terms',
        'field': f,
        'mincount': 1,
        'limit': 30,
        'allBuckets': True,
        'numBuckets': True,
        'facet':{
            'taxonID':{
                'type': 'terms',
                'field': 'taxonID',
                'limit': 30,
                'numBuckets': True,
            },
        } 
    }


taxon_fields = ['scientificName', 'common_name_c', 'alternative_name_c', 'synonyms', 'misapplied', 
 'kingdom', 'phylum', 'class', 'order', 'family', 'genus', 'species', 'kingdom_c', 
 'phylum_c', 'class_c', 'order_c', 'family_c', 'genus_c']

taxon_all_facets = {}
taxon_all_facets['facet'] = {}

for f in taxon_fields:
    taxon_all_facets['facet'][f] = {
            'type': 'terms',
            'field': f,
            'mincount': 1,
            'allBuckets': True,
            'numBuckets': False,
    }