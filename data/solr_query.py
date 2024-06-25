from conf.settings import env

SOLR_PREFIX = env('SOLR_PREFIX')

occ_fields = ['scientificName', 'common_name_c', 'alternative_name_c', 'synonyms', 'misapplied', 'sourceScientificName', 'sourceVernacularName', 'originalScientificName', 
              'kingdom', 'phylum', 'class', 'order', 'family', 'genus', 'species', 'kingdom_c', 'phylum_c', 'class_c', 'order_c', 'family_c', 'genus_c', 
              'rightsHolder', 'sensitiveCategory', 'locality', 'recordedBy', 'basisOfRecord', 'datasetName', 'license', 'eventDate']

col_fields = ['scientificName', 'common_name_c', 'alternative_name_c', 'synonyms', 'misapplied', 'sourceScientificName', 'sourceVernacularName', 'originalScientificName', 
              'kingdom', 'phylum', 'class', 'order', 'family', 'genus', 'species', 'kingdom_c', 'phylum_c', 'class_c', 'order_c', 'family_c', 'genus_c', 
              'rightsHolder', 'sensitiveCategory', 'locality', 'recordedBy', 'datasetName', 'license', 'eventDate', 'typeStatus', 'preservation']


def create_facet_list(record_type):
    if record_type == 'col':
        field_list = col_fields
    else:
        field_list = occ_fields
    facets = {}
    facets['facet'] = {}
    for f in field_list:
        facets['facet'][f] = {
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
    return facets


def create_taxon_facet_list():
    taxon_fields = ['scientificName', 'common_name_c', 'alternative_name_c', 'synonyms', 'misapplied', 
    'kingdom', 'phylum', 'class', 'order', 'family', 'genus', 'species', 'kingdom_c', 
    'phylum_c', 'class_c', 'order_c', 'family_c', 'genus_c']

    facets = {}
    facets['facet'] = {}

    for f in taxon_fields:
        facets['facet'][f] = {
                'type': 'terms',
                'field': f,
                'mincount': 1,
                'allBuckets': True,
                'numBuckets': False,
        }

    return facets

