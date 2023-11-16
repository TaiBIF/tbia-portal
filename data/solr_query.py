from conf.settings import env

SOLR_PREFIX = env('SOLR_PREFIX')

occ_facets = {  'facet': {
        'scientificName': {
            'type': 'terms',
            'field': 'scientificName',
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
        },
        'common_name_c': {
            'type': 'terms',
            'field': 'common_name_c',
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
        },
        'alternative_name_c': {
            'type': 'terms',
            'field': 'alternative_name_c',
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
        },
        'synonyms': {
            'type': 'terms',
            'field': 'synonyms',
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
        },
        'misapplied': {
            'type': 'terms',
            'field': 'misapplied',
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
        },
        'sourceScientificName': {
            'type': 'terms',
            'field': 'sourceScientificName',
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
        },
        'sourceVernacularName': {
            'type': 'terms',
            'field': 'sourceVernacularName',
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
        },
        'originalScientificName': {
            'type': 'terms',
            'field': 'originalScientificName',
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
        },
        'taxonRank': {
            'type': 'terms',
            'field': 'taxonRank',
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
                    }
                }
        },
        'kingdom': {
            'type': 'terms',
            'field': 'kingdom',
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
        },
        'phylum': {
            'type': 'terms',
            'field': 'phylum',
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
        },
        'class': {
            'type': 'terms',
            'field': 'class',
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
        },
        'order': {
            'type': 'terms',
            'field': 'order',
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
        },
        'family': {
            'type': 'terms',
            'field': 'family',
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
        },
        'genus': {
            'type': 'terms',
            'field': 'genus',
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
        },
        'species': {
            'type': 'terms',
            'field': 'species',
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
        },
        'kingdom_c': {
            'type': 'terms',
            'field': 'kingdom_c',
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
        },
        'phylum_c': {
            'type': 'terms',
            'field': 'phylum_c',
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
        },
        'class_c': {
            'type': 'terms',
            'field': 'class_c',
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
        },
        'order_c': {
            'type': 'terms',
            'field': 'order_c',
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
        },
        'family_c': {
            'type': 'terms',
            'field': 'family_c',
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
        },
        'genus_c': {
            'type': 'terms',
            'field': 'genus_c',
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
        },
        'rightsHolder': {
            'type': 'terms',
            'field': 'rightsHolder',
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
                    }
                }
        },
        'sensitiveCategory': {
            'type': 'terms',
            'field': 'sensitiveCategory',
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
                    }
                }
        },
        'locality': {
            'type': 'terms',
            'field': 'locality',
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
                    }
                }
        },
        'recordedBy': {
            'type': 'terms',
            'field': 'recordedBy',
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
                    }
                }
        },
        'basisOfRecord': {
            'type': 'terms',
            'field': 'basisOfRecord',
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
                    }
                }
        },
        'datasetName': {
            'type': 'terms',
            'field': 'datasetName',
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
                    }
                }
        },
        'license': {
            'type': 'terms',
            'field': 'license',
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
                    }
                }
        },
        'eventDate': {
            'type': 'terms',
            'field': 'eventDate',
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
        },
    },
}



col_facets = { 'facet': {
        'scientificName': {
            'type': 'terms',
            'field': 'scientificName',
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
        },
        'common_name_c': {
            'type': 'terms',
            'field': 'common_name_c',
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
        },
        'alternative_name_c': {
            'type': 'terms',
            'field': 'alternative_name_c',
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
        },
        'synonyms': {
            'type': 'terms',
            'field': 'synonyms',
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
        },
        'misapplied': {
            'type': 'terms',
            'field': 'misapplied',
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
        },
        'sourceScientificName': {
            'type': 'terms',
            'field': 'sourceScientificName',
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
        },
        'sourceVernacularName': {
            'type': 'terms',
            'field': 'sourceVernacularName',
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
        },
        'originalScientificName': {
            'type': 'terms',
            'field': 'originalScientificName',
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
        },
        'rightsHolder': {
            'type': 'terms',
            'field': 'rightsHolder',
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
        },
        'sensitiveCategory': {
            'type': 'terms',
            'field': 'sensitiveCategory',
            'mincount': 1,
            'limit': 30,
            'allBuckets': True,
            'numBuckets': True,
            'facet':{
                    'taxonID':{
                        'type': 'terms',
                        'field': 'taxonID',
                        'limit': 30,
                        'allBuckets': True,
                        'numBuckets': True,
                    },
                }
        },
        'taxonRank': {
            'type': 'terms',
            'field': 'taxonRank',
            'mincount': 1,
            'limit': 30,
            'allBuckets': True,
            'numBuckets': True,
            'facet':{
                    'taxonID':{
                        'type': 'terms',
                        'field': 'taxonID',
                        'limit': 30,
                        'allBuckets': True,
                        'numBuckets': True,
                    },
                }
        },
        'locality': {
            'type': 'terms',
            'field': 'locality',
            'mincount': 1,
            'limit': 30,
            'allBuckets': True,
            'numBuckets': True,
            'facet':{
                    'taxonID':{
                        'type': 'terms',
                        'field': 'taxonID',
                        'limit': 30,
                        'allBuckets': True,
                        'numBuckets': True,
                    },
                }
        },
        'recordedBy': {
            'type': 'terms',
            'field': 'recordedBy',
            'mincount': 1,
            'limit': 30,
            'allBuckets': True,
            'numBuckets': True,
            'facet':{
                    'taxonID':{
                        'type': 'terms',
                        'field': 'taxonID',
                        'limit': 30,
                        'allBuckets': True,
                        'numBuckets': True,
                    },
                }
        },
        'typeStatus': {
            'type': 'terms',
            'field': 'typeStatus',
            'mincount': 1,
            'limit': 30,
            'allBuckets': True,
            'numBuckets': True,
            'facet':{
                    'taxonID':{
                        'type': 'terms',
                        'field': 'taxonID',
                        'limit': 30,
                        'allBuckets': True,
                        'numBuckets': True,
                    },
                }
        },
        'preservation': {
            'type': 'terms',
            'field': 'preservation',
            'mincount': 1,
            'limit': 30,
            'allBuckets': True,
            'numBuckets': True,
            'facet':{
                    'taxonID':{
                        'type': 'terms',
                        'field': 'taxonID',
                        'limit': 30,
                        'allBuckets': True,
                        'numBuckets': True,
                    },
                }
        },
        'datasetName': {
            'type': 'terms',
            'field': 'datasetName',
            'mincount': 1,
            'limit': 30,
            'allBuckets': True,
            'numBuckets': True,
            'facet':{
                    'taxonID':{
                        'type': 'terms',
                        'field': 'taxonID',
                        'limit': 30,
                        'allBuckets': True,
                        'numBuckets': True,
                    },
                }
        },
        'license': {
            'type': 'terms',
            'field': 'license',
            'mincount': 1,
            'limit': 30,
            'allBuckets': True,
            'numBuckets': True,
            'facet':{
                    'taxonID':{
                        'type': 'terms',
                        'field': 'taxonID',
                        'limit': 30,
                        'allBuckets': True,
                        'numBuckets': True,
                    },
                }
        },

        'kingdom': {
            'type': 'terms',
            'field': 'kingdom',
            'mincount': 1,
            'limit': 30,
            'allBuckets': True,
            'numBuckets': True,
            'facet':{
                    'taxonID':{
                        'type': 'terms',
                        'field': 'taxonID',
                        'limit': 30,
                        'allBuckets': True,
                        'numBuckets': True,
                    },
                }
        },
        'phylum': {
            'type': 'terms',
            'field': 'phylum',
            'mincount': 1,
            'limit': 30,
            'allBuckets': True,
            'numBuckets': True,
            'facet':{
                    'taxonID':{
                        'type': 'terms',
                        'field': 'taxonID',
                        'limit': 30,
                        'allBuckets': True,
                        'numBuckets': True,
                    },
                }
        },
        'class': {
            'type': 'terms',
            'field': 'class',
            'mincount': 1,
            'limit': 30,
            'allBuckets': True,
            'numBuckets': True,
            'facet':{
                    'taxonID':{
                        'type': 'terms',
                        'field': 'taxonID',
                        'limit': 30,
                        'allBuckets': True,
                        'numBuckets': True,
                    },
                }
        },
        'order': {
            'type': 'terms',
            'field': 'order',
            'mincount': 1,
            'limit': 30,
            'allBuckets': True,
            'numBuckets': True,
            'facet':{
                    'taxonID':{
                        'type': 'terms',
                        'field': 'taxonID',
                        'limit': 30,
                        'allBuckets': True,
                        'numBuckets': True,
                    },
                }
        },
        'family': {
            'type': 'terms',
            'field': 'family',
            'mincount': 1,
            'limit': 30,
            'allBuckets': True,
            'numBuckets': True,
            'facet':{
                    'taxonID':{
                        'type': 'terms',
                        'field': 'taxonID',
                        'limit': 30,
                        'allBuckets': True,
                        'numBuckets': True,
                    },
                }
        },
        'genus': {
            'type': 'terms',
            'field': 'genus',
            'mincount': 1,
            'limit': 30,
            'allBuckets': True,
            'numBuckets': True,
            'facet':{
                    'taxonID':{
                        'type': 'terms',
                        'field': 'taxonID',
                        'limit': 30,
                        'allBuckets': True,
                        'numBuckets': True,
                    },
                }
        },
        'species': {
            'type': 'terms',
            'field': 'species',
            'mincount': 1,
            'limit': 30,
            'allBuckets': True,
            'numBuckets': True,
            'facet':{
                    'taxonID':{
                        'type': 'terms',
                        'field': 'taxonID',
                        'limit': 30,
                        'allBuckets': True,
                        'numBuckets': True,
                    },
                }
        },
        'kingdom_c': {
            'type': 'terms',
            'field': 'kingdom_c',
            'mincount': 1,
            'limit': 30,
            'allBuckets': True,
            'numBuckets': True,
            'facet':{
                    'taxonID':{
                        'type': 'terms',
                        'field': 'taxonID',
                        'limit': 30,
                        'allBuckets': True,
                        'numBuckets': True,
                    },
                }
        },
        'phylum_c': {
            'type': 'terms',
            'field': 'phylum_c',
            'mincount': 1,
            'limit': 30,
            'allBuckets': True,
            'numBuckets': True,
            'facet':{
                    'taxonID':{
                        'type': 'terms',
                        'field': 'taxonID',
                        'limit': 30,
                        'allBuckets': True,
                        'numBuckets': True,
                    },
                }
        },
        'class_c': {
            'type': 'terms',
            'field': 'class_c',
            'mincount': 1,
            'limit': 30,
            'allBuckets': True,
            'numBuckets': True,
            'facet':{
                    'taxonID':{
                        'type': 'terms',
                        'field': 'taxonID',
                        'limit': 30,
                        'allBuckets': True,
                        'numBuckets': True,
                    },
                }
        },
        'order_c': {
            'type': 'terms',
            'field': 'order_c',
            'mincount': 1,
            'limit': 30,
            'allBuckets': True,
            'numBuckets': True,
            'facet':{
                    'taxonID':{
                        'type': 'terms',
                        'field': 'taxonID',
                        'limit': 30,
                        'allBuckets': True,
                        'numBuckets': True,
                    },
                }
        },
        'family_c': {
            'type': 'terms',
            'field': 'family_c',
            'mincount': 1,
            'limit': 30,
            'allBuckets': True,
            'numBuckets': True,
            'facet':{
                    'taxonID':{
                        'type': 'terms',
                        'field': 'taxonID',
                        'limit': 30,
                        'allBuckets': True,
                        'numBuckets': True,
                    },
                }
        },
        'genus_c': {
            'type': 'terms',
            'field': 'genus_c',
            'mincount': 1,
            'limit': 30,
            'allBuckets': True,
            'numBuckets': True,
            'facet':{
                    'taxonID':{
                        'type': 'terms',
                        'field': 'taxonID',
                        'limit': 30,
                        'allBuckets': True,
                        'numBuckets': True,
                    },
                }
        },
        'eventDate': {
            'type': 'terms',
            'field': 'eventDate',
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
        },
    }}




taxon_all_facets = { 'facet': {
        'scientificName': {
            'type': 'terms',
            'field': 'scientificName',
            'mincount': 1,
            # 'limit': 30,
            'allBuckets': True,
            'numBuckets': False,
            # 'facet':{
            #     'taxonID':{
            #         'type': 'terms',
            #         'field': 'id',
            #         'limit': 30,
            #         'numBuckets': True,
            #     },
            # }        
        },
        'common_name_c': {
            'type': 'terms',
            'field': 'common_name_c',
            'mincount': 1,
            # 'limit': 30,
            'allBuckets': True,
            'numBuckets': False,
            # 'facet':{
            #     'taxonID':{
            #         'type': 'terms',
            #         'field': 'id',
            #         'limit': 30,
            #         'numBuckets': True,
            #     },
            # }
        },
        'alternative_name_c': {
            'type': 'terms',
            'field': 'alternative_name_c',
            'mincount': 1,
            'limit': 30,
            'allBuckets': True,
            'numBuckets': True,
            'facet':{
                    'taxonID':{
                        'type': 'terms',
                        'field': 'id',
                        'limit': 30,
                        'numBuckets': True,
                    },
                }
        },
        'synonyms': {
            'type': 'terms',
            'field': 'synonyms',
            'mincount': 1,
            # 'limit': 30,
            'allBuckets': True,
            'numBuckets': False,
            # 'facet':{
            #         'taxonID':{
            #             'type': 'terms',
            #             'field': 'id',
            #             'limit': 30,
            #             'numBuckets': True,
            #         },
            #     }
        },
        'misapplied': {
            'type': 'terms',
            'field': 'misapplied',
            'mincount': 1,
            # 'limit': 30,
            'allBuckets': True,
            'numBuckets': False,
            # 'facet':{
            #         'taxonID':{
            #             'type': 'terms',
            #             'field': 'id',
            #             'limit': 30,
            #             'numBuckets': True,
            #         },
            #     }
        },
        'kingdom': {
            'type': 'terms',
            'field': 'kingdom',
            'mincount': 1,
            # 'limit': 30,
            'allBuckets': True,
            'numBuckets': False,
            # 'facet':{
            #         'taxonID':{
            #             'type': 'terms',
            #             'field': 'id',
            #             'limit': 30,
            #             'allBuckets': True,
            #             'numBuckets': True,
            #         },
            #     }
        },
        'phylum': {
            'type': 'terms',
            'field': 'phylum',
            'mincount': 1,
            # 'limit': 30,
            'allBuckets': True,
            'numBuckets': False,
            # 'facet':{
            #         'taxonID':{
            #             'type': 'terms',
            #             'field': 'id',
            #             'limit': 30,
            #             'allBuckets': True,
            #             'numBuckets': True,
            #         },
            #     }
        },
        'class': {
            'type': 'terms',
            'field': 'class',
            'mincount': 1,
            # 'limit': 30,
            'allBuckets': True,
            'numBuckets': False,
            # 'facet':{
            #         'taxonID':{
            #             'type': 'terms',
            #             'field': 'id',
            #             'limit': 30,
            #             'allBuckets': True,
            #             'numBuckets': True,
            #         },
            #     }
        },
        'order': {
            'type': 'terms',
            'field': 'order',
            'mincount': 1,
            # 'limit': 30,
            'allBuckets': True,
            'numBuckets': False,
            # 'facet':{
            #         'taxonID':{
            #             'type': 'terms',
            #             'field': 'id',
            #             'limit': 30,
            #             'allBuckets': True,
            #             'numBuckets': True,
            #         },
            #     }
        },
        'family': {
            'type': 'terms',
            'field': 'family',
            'mincount': 1,
            # 'limit': 30,
            'allBuckets': True,
            'numBuckets': False,
            # 'facet':{
            #         'taxonID':{
            #             'type': 'terms',
            #             'field': 'id',
            #             'limit': 30,
            #             'allBuckets': True,
            #             'numBuckets': True,
            #         },
            #     }
        },
        'genus': {
            'type': 'terms',
            'field': 'genus',
            'mincount': 1,
            # 'limit': 30,
            'allBuckets': True,
            'numBuckets': False,
            # 'facet':{
            #         'taxonID':{
            #             'type': 'terms',
            #             'field': 'id',
            #             'limit': 30,
            #             'allBuckets': True,
            #             'numBuckets': True,
            #         },
            #     }
        },
        'species': {
            'type': 'terms',
            'field': 'species',
            'mincount': 1,
            # 'limit': 30,
            'allBuckets': True,
            'numBuckets': False,
            # 'facet':{
            #         'taxonID':{
            #             'type': 'terms',
            #             'field': 'id',
            #             'limit': 30,
            #             'allBuckets': True,
            #             'numBuckets': True,
            #         },
            #     }
        },
        'kingdom_c': {
            'type': 'terms',
            'field': 'kingdom_c',
            'mincount': 1,
            # 'limit': 30,
            'allBuckets': True,
            'numBuckets': False,
            # 'facet':{
            #         'taxonID':{
            #             'type': 'terms',
            #             'field': 'id',
            #             'limit': 30,
            #             'allBuckets': True,
            #             'numBuckets': True,
            #         },
            #     }
        },
        'phylum_c': {
            'type': 'terms',
            'field': 'phylum_c',
            'mincount': 1,
            # 'limit': 30,
            'allBuckets': True,
            'numBuckets': False,
            # 'facet':{
            #         'taxonID':{
            #             'type': 'terms',
            #             'field': 'id',
            #             'limit': 30,
            #             'allBuckets': True,
            #             'numBuckets': True,
            #         },
            #     }
        },
        'class_c': {
            'type': 'terms',
            'field': 'class_c',
            'mincount': 1,
            # 'limit': 30,
            'allBuckets': True,
            'numBuckets': False,
            # 'facet':{
            #         'taxonID':{
            #             'type': 'terms',
            #             'field': 'id',
            #             'limit': 30,
            #             'allBuckets': True,
            #             'numBuckets': True,
            #         },
            #     }
        },
        'order_c': {
            'type': 'terms',
            'field': 'order_c',
            'mincount': 1,
            # 'limit': 30,
            'allBuckets': True,
            'numBuckets': False,
            # 'facet':{
            #         'taxonID':{
            #             'type': 'terms',
            #             'field': 'id',
            #             'limit': 30,
            #             'allBuckets': True,
            #             'numBuckets': True,
            #         },
            #     }
        },
        'family_c': {
            'type': 'terms',
            'field': 'family_c',
            'mincount': 1,
            # 'limit': 30,
            'allBuckets': True,
            'numBuckets': False,
            # 'facet':{
            #         'taxonID':{
            #             'type': 'terms',
            #             'field': 'id',
            #             'limit': 30,
            #             'allBuckets': True,
            #             'numBuckets': True,
            #         },
            #     }
        },
        'genus_c': {
            'type': 'terms',
            'field': 'genus_c',
            'mincount': 1,
            # 'limit': 30,
            'allBuckets': True,
            'numBuckets': False,
            # 'facet':{
            #         'taxonID':{
            #             'type': 'terms',
            #             'field': 'id',
            #             'limit': 30,
            #             'allBuckets': True,
            #             'numBuckets': True,
            #         },
            #     }
        },
    }}





