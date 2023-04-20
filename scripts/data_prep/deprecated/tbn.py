# test for TBN API

from numpy import nan
import requests
import pandas as pd
from data.models import *
from datetime import datetime, tzinfo,timedelta
from dateutil import parser

# nohup python -u manage.py shell < /Users/taibif/Documents/GitHub/tbia-portal/scripts/tbn.py &

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

# --------------
# get all occurrence data by datasetUUID
# --------------

# request_url = 'https://www.tbn.org.tw/api/v2/dataset'
# response = requests.get(request_url)

# data = response.json()

# i = 0
# total_data = data["data"]
# while data['links']['next'] != "":
#     print(i)
#     request_url = data['links']['next']
#     response = requests.get(request_url)
#     data = response.json()
#     total_data += data["data"]
#     i += 1

# datasets = []
# for i in range(len(total_data)):
#     print(i)
#     tmp = {'datasetUUID': total_data[i]['datasetUUID'],
#            'datasetName': total_data[i]['datasetName'],
#            'from': total_data[i]['datasetDataFrom'],
#            'import': total_data[i]['datasetLastImport'],
#            'create': total_data[i]['datasetCreated']}
#     datasets.append(tmp),

# pd.DataFrame(datasets).to_csv('../tbia-volumes/data/tbn_dataset.csv', encoding='utf-8-sig')

datasets = pd.read_csv('../tbia-volumes/data/tbn_dataset.csv', encoding='utf-8-sig')
taibif = pd.read_csv('../tbia-volumes/data/ipt-dataset-list.csv')
rank = pd.read_csv('../tbia-volumes/data/taxa_c.csv', names=['rank_c','rank'])

# remove duplicated dataset that uploaded through taibif ipt
taibif_uuid = taibif.guid.unique().tolist()
taibif_uuid = [i for i in taibif_uuid if i is not nan]
datasets = datasets[~datasets.datasetUUID.isin(taibif_uuid)] # 967

dataset_uuid = datasets.datasetUUID.tolist()

# remove 國家公園 & 濕地資料庫 4caf0c2f-25ad-4898-a1e6-5346457f0233 / 7e5a68cc-771e-42ef-8cf7-b68f2254d15b
dataset_uuid.remove('4caf0c2f-25ad-4898-a1e6-5346457f0233')
dataset_uuid.remove('7e5a68cc-771e-42ef-8cf7-b68f2254d15b')

# remove already finished dataset
dataset_uuid.remove('79ae93e0-a2b8-11de-9f79-b8a03c50a862')

# remove ebird
dataset_uuid.remove('4fa7b334-ce0d-4e88-aaae-2e0c138d049e')

dataset_uuid.sort() 

for i in range(len(dataset_uuid)):
    uuid = dataset_uuid[i]
    print(f"get {uuid}, {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    dataset_name = datasets[datasets['datasetUUID']==uuid].datasetName.values[0]
    request_url = f"https://www.tbn.org.tw/api/v2/occurrence?datasetUUID={uuid}"
    response = requests.get(request_url)
    data = response.json()
    len_of_data = data['meta']['total'] # 6846187 -> 22820
    j = 0
    total_data = data["data"]
    while data['links']['next'] != "":
        print(f"{uuid}, get data {j}, {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        request_url = data['links']['next']
        response = requests.get(request_url)
        data = response.json()
        total_data += data["data"]
        j += 1
        # if j != 0 and j % 300 == 0:
        #     df = pd.DataFrame(total_data)
        #     df.to_csv(f"../tbia-volumes/tbn_data/{uuid}_{j/300}.csv")
        #     total_data = []
    df = pd.DataFrame(total_data)
    df.to_csv(f"../tbia-volumes/tbn_data/{uuid}.csv")


# ebird
uuid = '4fa7b334-ce0d-4e88-aaae-2e0c138d049e'
print(f"get ebird, {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
dataset_name = datasets[datasets['datasetUUID']==uuid].datasetName.values[0]
request_url = f"https://www.tbn.org.tw/api/v2/occurrence?datasetUUID={uuid}"
response = requests.get(request_url)
data = response.json()
len_of_data = data['meta']['total'] # 6846187 -> 22820
j = 0
total_data = data["data"]
while data['links']['next'] != "":
    print(f"ebird, get data {j}, {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    request_url = data['links']['next']
    response = requests.get(request_url)
    data = response.json()
    total_data += data["data"]
    j += 1
    if j != 0 and j % 300 == 0:
        df = pd.DataFrame(total_data)
        df.to_csv(f"../tbia-volumes/tbn_data/{uuid}_{j/300}.csv")
        total_data = []
df = pd.DataFrame(total_data)
df.to_csv(f"../tbia-volumes/tbn_data/{uuid}.csv")

# collection test file
uuid = '97c21d3f-774b-45e7-9149-4c0697fadbde'
print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
dataset_name = '臺灣特有生物研究保育中心植物標本館(TAIE)苔蘚資料'
request_url = f"https://www.tbn.org.tw/api/v2/occurrence?datasetUUID={uuid}"
response = requests.get(request_url)
data = response.json()
len_of_data = data['meta']['total'] # 6846187 -> 22820
j = 0
total_data = data["data"]
while data['links']['next'] != "":
    print(j)
    print(f"get data {j}, {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    request_url = data['links']['next']
    response = requests.get(request_url)
    data = response.json()
    total_data += data["data"]
    j += 1
    # if j != 0 and j % 300 == 0:
    #     df = pd.DataFrame(total_data)
    #     df.to_csv(f"../tbia-volumes/tbn_data/{uuid}_{j/300}.csv")
    #     total_data = []
df = pd.DataFrame(total_data)
df.to_csv(f"../tbia-volumes/tbn_data/{uuid}.csv")

    # for k in range(len(df)):
    #     print(f"{dataset_name}, {k}, {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    #     row = df.iloc[k]
    #     taxon_id, sensitiveState, name_code, precision, data_generalize = None, None, None, row.coordinatePrecision, None
    #     # NomenMatch
    #     request_url = f"http://match.taibif.tw/api.php?names={row.scientificName}&best=yes&format=json"
    #     response = requests.get(request_url)
    #     res = response.json()['results'][0][0]
    #     if res['best']:
    #         if res['best']:
    #             taxon_id = res['best'].get('tbn',None)
    #             # get sensitive state & taicol name code
    #             # !!! need to change if use taicol taxon in the future !!!
    #             if taxon_id:
    #                 request_url = f"https://www.tbn.org.tw/api/v2/species?uuid={taxon_id}"
    #                 response = requests.get(request_url)
    #                 t = response.json()['data']
    #                 if t:
    #                     name_code = t[0]['taicolNameCode']
    #                     sensitiveState = t[0]['sensitiveState']
    #                     if sensitiveState == '輕度':
    #                         precision = 0.01
    #                         data_generalize = True
    #                     elif sensitiveState == '重度':
    #                         precision = 0.1
    #                         data_generalize = True
    #                     taxon_rank = t[0]['taxonRank']
    #                     rank_e = rank[rank['rank_c']==taxon_rank]['rank'].values[0] if taxon_rank in rank.rank_c.to_list() else None
    #     # check dataset belongs to occurrence or collection
    #     # PreservedSpecimen, FossilSpecimen, LivingSpecimen, MaterialSample, Event, HumanObservation, MachineObservation, Taxon, Occurrence, MaterialCitation
    #     if 'Specimen' not in row.basisOfRecord:
    #         Occurrence.objects.create(
    #             rightsHolder = 'TBN',
    #             taxonUUID = taxon_id,
    #             originalModified = convert_date(row.modified),
    #             originalCreated = convert_date(row.created),
    #             occurrenceID = row.occurrenceUUID,
    #             originalScientificName = row.scientificName,
    #             originalVernacularName = row.vernacularName,
    #             sensitiveCategory = sensitiveState,
    #             taxonRank = rank_e,
    #             eventDate = row.eventDate,
    #             standardDate = convert_date(row.eventDate),
    #             verbatimLongitude = row.decimalLongitude,
    #             verbatimLatitude = row.decimalLatitude,
    #             verbatimCoordinateSystem = 'decimalDegrees' if row.decimalLongitude and row.decimalLatitude else None,
    #             verbatimSRS = 'WGS84' if row.decimalLongitude and row.decimalLatitude else None,
    #             standardLongitude = float(row.decimalLongitude) if row.decimalLongitude not in ['', None] else None,
    #             standardLatitude = float(row.decimalLatitude) if row.decimalLatitude not in ['', None] else None,
    #             dataGeneralizations = data_generalize,
    #             coordinateUncertaintyInMeters = row.coordinateUncertaintyInMeters,
    #             coordinatePrecision = precision,
    #             locality = row.eventPlaceAdminarea,
    #             organismQuantity = row.organismQuantityType if row.individualCount == '' else row.individualCount,
    #             organismQuantityType = row.organismQuantityType, 
    #             scientificNameID = name_code,
    #             basisOfRecord = row.basisOfRecord,
    #             datasetName = row.datasetName,
    #             resourceContacts = row.datasetAuthor,
    #             references = f"https://www.tbn.org.tw/occurrence/{row.tbnID}"
    #         )
    #     else:
    #         Collection.objects.create(
    #             occurrenceID = row.occurrenceUUID,
    #             rightsHolder = 'TBN',
    #             taxonUUID = taxon_id,
    #             originalScientificName = row.scientificName,
    #             originalVernacularName = row.vernacularName,
    #             taxonRank = rank_e,
    #             eventDate = row.eventDate,
    #             standardDate = convert_date(row.eventDate),
    #             verbatimLongitude = row.decimalLongitude,
    #             verbatimLatitude = row.decimalLatitude,
    #             verbatimCoordinateSystem = 'decimalDegrees' if row.decimalLongitude and row.decimalLatitude else None,
    #             verbatimSRS = 'WGS84' if row.decimalLongitude and row.decimalLatitude else None,
    #             standardLongitude = float(row.decimalLongitude) if row.decimalLongitude not in ['', None] else None,
    #             standardLatitude = float(row.decimalLatitude) if row.decimalLatitude not in ['', None] else None,
    #             dataGeneralizations = data_generalize,
    #             coordinateUncertaintyInMeters = row.coordinateUncertaintyInMeters,
    #             coordinatePrecision = precision,
    #             locality = row.eventPlaceAdminarea,
    #             organismQuantity = row.organismQuantityType if row.individualCount == '' else row.individualCount,
    #             organismQuantityType = row.organismQuantityType, 
    #             scientificNameID = name_code,
    #             datasetName = row.datasetName,
    #             resourceContacts = row.datasetAuthor,
    #             references = f"https://www.tbn.org.tw/occurrence/{row.tbnID}",
    #             sensitiveCategory = sensitiveState,
    #             originalModified = convert_date(row.modified),
    #             originalCreated = convert_date(row.created),
    #         )
