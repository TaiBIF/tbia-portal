
from numpy import nan
import requests
import pandas as pd
from data.models import *
from datetime import datetime, tzinfo,timedelta
from dateutil import parser
import time

import sys
dataset_uuid = sys.argv[0]

def convert_date(date):
    formatted_date = None
    if date != '' and date is not None:
        try:
            formatted_date = parser.parse(date) 
        except parser._parser.ParserError:
            formatted_date = datetime.fromtimestamp(int(date))
        except:
            formatted_date = None
    return formatted_date

rank = pd.read_csv('../tbia-volumes/data/taxa_c.csv', names=['rank_c','rank'])
df = pd.read_csv('../tbia-volumes/tbn_data/{dataset_uuid}.csv', encoding='utf-8-sig')

for k in range(len(df)):
    print(f"{k}, {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    time.sleep(1) # prevent disconnect from TBN
    row = df.iloc[k]
    taxon_id, sensitiveState, name_code, precision, data_generalize = None, None, None, row.coordinatePrecision, None
    # NomenMatch
    request_url = f"http://match.taibif.tw/api.php?names={row.scientificName}&best=yes&format=json"
    response = requests.get(request_url)
    res = response.json()['results'][0][0]
    if res['best']:
        if res['best']:
            taxon_id = res['best'].get('tbn',None)
            # get sensitive state & taicol name code
            # !!! need to change if use taicol taxon in the future !!!
            if taxon_id:
                request_url = f"https://www.tbn.org.tw/api/v2/species?uuid={taxon_id}"
                response = requests.get(request_url)
                t = response.json()['data']
                if t:
                    name_code = t[0]['taicolNameCode']
                    sensitiveState = t[0]['sensitiveState']
                    if sensitiveState == '輕度':
                        precision = 0.01
                        data_generalize = True
                    elif sensitiveState == '重度':
                        precision = 0.1
                        data_generalize = True
                    taxon_rank = t[0]['taxonRank']
                    rank_e = rank[rank['rank_c']==taxon_rank]['rank'].values[0] if taxon_rank in rank.rank_c.to_list() else None
    # check dataset belongs to occurrence or collection
    # PreservedSpecimen, FossilSpecimen, LivingSpecimen, MaterialSample, Event, HumanObservation, MachineObservation, Taxon, Occurrence, MaterialCitation
    if 'Specimen' not in row.basisOfRecord:
        Occurrence.objects.create(
            rightsHolder = 'TBN',
            taxonUUID = taxon_id,
            originalModified = convert_date(row.modified),
            originalCreated = convert_date(row.created),
            occurrenceID = row.occurrenceUUID,
            originalScientificName = row.scientificName,
            originalVernacularName = row.vernacularName,
            sensitiveCategory = sensitiveState,
            taxonRank = rank_e,
            eventDate = row.eventDate,
            standardDate = convert_date(row.eventDate),
            verbatimLongitude = row.decimalLongitude,
            verbatimLatitude = row.decimalLatitude,
            verbatimCoordinateSystem = 'decimalDegrees' if row.decimalLongitude and row.decimalLatitude else None,
            verbatimSRS = 'WGS84' if row.decimalLongitude and row.decimalLatitude else None,
            standardLongitude = float(row.decimalLongitude) if row.decimalLongitude not in ['', None] else None,
            standardLatitude = float(row.decimalLatitude) if row.decimalLatitude not in ['', None] else None,
            dataGeneralizations = data_generalize,
            coordinateUncertaintyInMeters = row.coordinateUncertaintyInMeters,
            coordinatePrecision = precision,
            locality = row.eventPlaceAdminarea,
            organismQuantity = row.organismQuantityType if row.individualCount == '' else row.individualCount,
            organismQuantityType = row.organismQuantityType, 
            scientificNameID = name_code,
            basisOfRecord = row.basisOfRecord,
            datasetName = row.datasetName,
            resourceContacts = row.datasetAuthor,
            references = f"https://www.tbn.org.tw/occurrence/{row.tbnID}"
        )
    else:
        Collection.objects.create(
            occurrenceID = row.occurrenceUUID,
            rightsHolder = 'TBN',
            taxonUUID = taxon_id,
            originalScientificName = row.scientificName,
            originalVernacularName = row.vernacularName,
            taxonRank = rank_e,
            eventDate = row.eventDate,
            standardDate = convert_date(row.eventDate),
            verbatimLongitude = row.decimalLongitude,
            verbatimLatitude = row.decimalLatitude,
            verbatimCoordinateSystem = 'decimalDegrees' if row.decimalLongitude and row.decimalLatitude else None,
            verbatimSRS = 'WGS84' if row.decimalLongitude and row.decimalLatitude else None,
            standardLongitude = float(row.decimalLongitude) if row.decimalLongitude not in ['', None] else None,
            standardLatitude = float(row.decimalLatitude) if row.decimalLatitude not in ['', None] else None,
            dataGeneralizations = data_generalize,
            coordinateUncertaintyInMeters = row.coordinateUncertaintyInMeters,
            coordinatePrecision = precision,
            locality = row.eventPlaceAdminarea,
            organismQuantity = row.organismQuantityType if row.individualCount == '' else row.individualCount,
            organismQuantityType = row.organismQuantityType, 
            scientificNameID = name_code,
            datasetName = row.datasetName,
            resourceContacts = row.datasetAuthor,
            references = f"https://www.tbn.org.tw/occurrence/{row.tbnID}",
            sensitiveCategory = sensitiveState,
            originalModified = convert_date(row.modified),
            originalCreated = convert_date(row.created),
        )
