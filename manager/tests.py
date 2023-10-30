from django.test import TestCase

# Create your tests here.

from manager.models import *

# df = pd.read_csv('/tbia-volumes/bucket/duplicated_data.csv')


# tesri = df[df.group=='tesri']
# tesri = tesri.reset_index(drop=True)

# not_eq = []
# for i in tesri.index:
#     print(i)
#     row = tesri.iloc[i]
#     ml = MatchLog.objects.filter(occurrenceID=row.occurrenceID).values()
#     a_id = ml[0]['id']
#     a = ml[0]
#     a.pop('id')
#     b = ml[1]
#     b.pop('id')
#     if a == b:
#         MatchLog.objects.get(id=a_id).delete()
#     else:
#         not_eq.append(row.occurrenceID)


# gbif = df[df.group=='gbif']
# gbif = gbif.reset_index(drop=True)
import pandas as pd
import subprocess
import requests

url = 'http://host.docker.internal:8983/solr/tbia_records/select?facet.field=occurrenceID&facet.mincount=2&facet=true&fq=group%3Agbif&indent=true&q.op=OR&q=*%3A*&rows=0&facet.limit=-1'
# url = 'http://127.0.0.1:8983/solr/tbia_records/select?facet.field=occurrenceID&facet.mincount=2&facet=true&fq=group%3Agbif&indent=true&q.op=OR&q=*%3A*&rows=0&facet.limit=-1'

gbif = requests.get(url)
resp = gbif.json()
resp = resp['facet_counts']['facet_fields']['occurrenceID']
count_list = [resp[x+1] for x in range(0, len(resp),2)]

all(i == 2 for i in count_list)
gbif_list = [resp[x] for x in range(0, len(resp),2)]

not_eq = []
for g in gbif_list:
    url = f'http://host.docker.internal:8983/solr/tbia_records/select?q=occurrenceID:{g}'
    rr = requests.get(url)
    result = rr.json()
    result['response']['docs'][0].pop('_version_')
    result['response']['docs'][0].pop('sourceModified')
    result['response']['docs'][0].pop('modified')
    result['response']['docs'][0].pop('created')
    id_a = result['response']['docs'][0].pop('id')
    a = result['response']['docs'][0]
    result['response']['docs'][1].pop('_version_')
    result['response']['docs'][1].pop('sourceModified')
    result['response']['docs'][1].pop('modified')
    result['response']['docs'][1].pop('created')
    id_b = result['response']['docs'][1].pop('id')
    b = result['response']['docs'][1]
    if a == b:
        comm = f""" curl http://host.docker.internal:8983/solr/tbia_records/update?commit=true -X POST -H "Content-Type: text/xml" --data-binary "<delete><query>id:{id_a}</query></delete>" """
        process = subprocess.Popen(comm, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        process.communicate()
    else:
        not_eq.append(g)

not_df = pd.DataFrame({'tbiaID': not_eq})
not_df.to_csv('gbif_no_eq.csv', index=None)

# not_eq = []
# deleted_id = []
# for i in gbif_list:
#     print(i)
#     # row = gbif.iloc[i]
#     ml = MatchLog.objects.filter(occurrenceID=i).values()
#     a_id = ml[0]['id']
#     a = ml[0]
#     a.pop('id')
#     b = ml[1]
#     b.pop('id')
#     if a == b:
#         delete_id = MatchLog.objects.get(id=a_id).tbiaID
#         MatchLog.objects.get(id=a_id).delete()
#         deleted_id.append(delete_id)
#     else:
#         not_eq.append(i)


# not_df = pd.DataFrame({'tbiaID': not_eq})

# not_df.to_csv('gbif_no_eq.csv', index=None)




# # TODO 這邊要刪掉solr內的資料

# deleted_df = pd.DataFrame({'tbiaID': deleted_id})

# deleted_df.to_csv('gbif_delete.csv', index=None)

# &facet.field=group&facet.field=datasetName

# url = "http://solr:8983/solr/tbia_records/select?facet.pivot=rightsHolder,datasetName&facet=true&indent=true&q.op=OR&q=standardDate%3A%5B1970-01-01T00%3A00%3A00Z%20TO%201970-01-01T00%3A00%3A00Z%5D"



# data['facet_counts']['facet_pivot']['group,datasetName']

# {'field': 'group', 'value': 'forest', 'count': 249759, 'pivot': [{'field': 'datasetName', 'value': '建立國家生物多樣性指標及特定生物類群族群變化監測模式(3/3)', 'count': 72960}, {'field': 'datasetName', 'value': '台灣蛙類野外族群趨勢監測研究', 'count': 32720}, {'field': 'datasetName', 'value': '「101年度鰲鼓濕地森林園區鳥類監測及建立監測模式」', 'count': 24952}, {'field': 'datasetName', 'value': '第三次森林資源調查', 'count': 24949}, {'field': 'datasetName', 'value': '102年度鰲鼓濕地森林園區鳥類監測及建立監測模式', 'count': 13909}, {'field': 'datasetName', 'value': '因應氣候變遷生物多樣性回復力之研究(1/3)- 以大白山至大南澳嶺與雙溪、頭城山區為例', 'count': 10246}, {'field': 'datasetName', 'value': '林田山事業區第142林班動物資源調查暨社區參與監測計畫', 'count': 8077}, {'field': 'datasetName', 'value': '雪霸自然保護區植物資源調查（二） 志樂溪流域植相及植群調查', 'count': 6973}, {'field': 'datasetName', 'value': '十八羅漢山自然保護區暨旗山事業區第55林班陸域脊椎動物相調查及永久樣區監測計劃', 'count': 5986}, {'field': 'datasetName', 'value': '台11線海線北段生態系服務盤點專業服務委辦計畫(2/2)', 'count': 5521}, {'field': 'datasetName', 'value': '利嘉溪、大南溪流域河川生態系服務盤點專業服務委辦計畫(2/2)', 'count': 4296}, {'field': 'datasetName', 'value': '新竹處轄重點工程生態資源調查工作委託專業服務', 'count': 3969}, {'field': 'datasetName', 'value': '生物資源資料庫', 'count': 3077}, {'field': 'datasetName', 'value': '110年大雪山區域鳥類資源保育推廣計畫', 'count': 2852}, {'field': 'datasetName', 'value': '全國森林濕地多樣性調查及監測計畫（3/3）', 'count': 2600}, {'field': 'datasetName', 'value': '東方蜂鷹移動行為之研究(2/2) ', 'count': 2376}, {'field': 'datasetName', 'value': '全國森林濕地多樣性調查及監測計畫（1/3）', 'count': 2305}, {'field': 'datasetName', 'value': '外來種斑腿樹蛙控制與監測計畫', 'count': 2159}, {'field': 'datasetName', 'value': '高海拔山區草原生態系變遷調查(1/2)', 'count': 2115}, {'field': 'datasetName', 'value': '利嘉野生動物重要棲息環境哺乳類與鳥類資源調查與監測(二)', 'count': 1970}, {'field': 'datasetName', 'value': '臺東縣轄海岸山脈野生動物重要棲息環境及周遭緩衝區（成功事業區第40林班至45林班） 動物資源調查與監測計畫（1/3）', 'count': 1878}, {'field': 'datasetName', 'value': '全國森林濕地多樣性調查及監測計畫（2/3）', 'count': 1700}, {'field': 'datasetName', 'value': '大鬼湖重要濕地(國家級)基礎調查', 'count': 1524}, {'field': 'datasetName', 'value': '臺灣黑熊分布預測模式及保育行動綱領之建立', 'count': 1017}, {'field': 'datasetName', 'value': '台灣產球背象鼻蟲之生態調查', 'count': 943}, {'field': 'datasetName', 'value': '105年水雉生態教育園區工作計畫書', 'count': 746}, {'field': 'datasetName', 'value': '花蓮縣平地造林區森林性動物監測計畫', 'count': 672}, {'field': 'datasetName', 'value': '104年水雉生態教育園區工作計畫書', 'count': 662}, {'field': 'datasetName', 'value': '海岸山脈野生動物重要棲息環境及周遭緩衝區（成功事業區第40-45林班、秀姑巒事業區第70、71林班）動物資源調查與監測計畫（2/2）', 'count': 604}, {'field': 'datasetName', 'value': '貴重木監測自動判釋(1/3)', 'count': 554}, {'field': 'datasetName', 'value': '103年水雉生態教育園區工作計畫書', 'count': 451}, {'field': 'datasetName', 'value': '出雲山自然保留區陸域脊椎動物相調查(2/3)', 'count': 419}, {'field': 'datasetName', 'value': '冷凍遺傳物質典藏中心之營運與遺傳物質之利用(3/3)', 'count': 402}, {'field': 'datasetName', 'value': '臺灣穗花杉遺傳單元調查與保育行動方案(2/2)', 'count': 383}, {'field': 'datasetName', 'value': '雪霸自然保護區植物資源調查（一）植物資源清單建立與維護－植物名錄', 'count': 323}, {'field': 'datasetName', 'value': '十八羅漢山自然保護區昆蟲相調查研究計畫', 'count': 314}, {'field': 'datasetName', 'value': '臺灣穗花杉遺傳單元調查與保育行動方案(1/2)', 'count': 295}, {'field': 'datasetName', 'value': '國有林班地區域野生動物道路致死調查及改善對策探討', 'count': 264}, {'field': 'datasetName', 'value': '臺中市政府水利局委託專業服務新社區食水嵙溪番社嶺橋段臺灣白魚監測作業 (第一期) 2016-2017', 'count': 261}, {'field': 'datasetName', 'value': '臺灣鳥類生產力與存活率監測', 'count': 254}, {'field': 'datasetName', 'value': '海岸山脈野生動物重要棲息環境及周遭緩衝區（成功事業區第40-45林班、秀姑巒事業區第70、71林班）動物資源調查與監測計畫（1/2）', 'count': 239}, {'field': 'datasetName', 'value': '貢寮水梯田國土生態綠網保育計畫', 'count': 201}, {'field': 'datasetName', 'value': '出雲山自然保留區陸域脊椎動物相調查(1/3)', 'count': 170}, {'field': 'datasetName', 'value': '臺中市政府水利局委託專業服務 新社區食水嵙溪番社嶺橋段臺灣白魚監測作業 (第二期)', 'count': 151}, {'field': 'datasetName', 'value': '丹大野生動物重要棲息環境 中大型野生動物族群監測', 'count': 149}, {'field': 'datasetName', 'value': ' 109年大雪山飛羽10週年賞鳥大賽及鳥類保育推廣工作', 'count': 143}, {'field': 'datasetName', 'value': '雪山坑溪野生動物重要棲息環境生物多樣性與指標生物監測模式：哺乳類與鳥類', 'count': 142}, {'field': 'datasetName', 'value': '林務局國家森林遊樂區物候監測研究計畫', 'count': 112}, {'field': 'datasetName', 'value': '浸水營地區(屏東縣轄)特有森林植物之伴生植食性昆蟲調查研究計畫', 'count': 98}, {'field': 'datasetName', 'value': '利用保育類動物-保育類鳥類共100隻', 'count': 95}, {'field': 'datasetName', 'value': '花蓮地區鳥類長期監測研究計畫', 'count': 93}, {'field': 'datasetName', 'value': '台灣真菌地理分布系統資料庫之建制與應用(2/4)', 'count': 88}, {'field': 'datasetName', 'value': '猛禽救傷繫放', 'count': 83}, {'field': 'datasetName', 'value': '出雲山自然保留區陸域脊椎動物相調查(3/3)', 'count': 59}, {'field': 'datasetName', 'value': '110年度嘉義林區管理處野生動物重要棲息環境蝙蝠監測暨自動相機監測資料分析計畫', 'count': 50}, {'field': 'datasetName', 'value': '保育類物種利用申請案生物出現紀錄', 'count': 42}, {'field': 'datasetName', 'value': '106年水雉生態教育園區工作計畫書', 'count': 41}, {'field': 'datasetName', 'value': '二水、名間地區台灣獼猴生態及作物危害調查', 'count': 38}, {'field': 'datasetName', 'value': '雙流國家森林遊樂區內特色動物之棲地利用及活動範圍之研究', 'count': 28}, {'field': 'datasetName', 'value': '山麻雀保育行動計畫 (二)', 'count': 17}, {'field': 'datasetName', 'value': '台灣大田鱉棲地資源調查及行為觀察研究', 'count': 14}, {'field': 'datasetName', 'value': '彰化近海海岸地大杓鷸繫放及衛星追蹤調查計畫', 'count': 9}, {'field': 'datasetName', 'value': '台灣熊鷹長期監測系統建立(二)', 'count': 5}, {'field': 'datasetName', 'value': '國家植群多樣性調查及製圖計畫', 'count': 5}, {'field': 'datasetName', 'value': '森氏杜鵑等菌根苗之培育及復育', 'count': 3}, {'field': 'datasetName', 'value': '107年水雉生態教育園區工作計畫', 'count': 2}, {'field': 'datasetName', 'value': '2021台灣北部都會區猛禽監測計畫', 'count': 1}, {'field': 'datasetName', 'value': '保育類野生動物利用-105中區野生動物及產製品型態鑑定實驗室-標本維護及研發野生動物標示方式', 'count': 1}, {'field': 'datasetName', 'value': '保育類野生動物利用-亞洲黑熊(台灣黑熊)、大貓熊、馬來熊、棕熊，黑熊域外保育復育計畫', 'count': 1}, {'field': 'datasetName', 'value': '穿山甲之族群評估、照養管理與保育教育推動', 'count': 1}]}

# final_d = pd.DataFrame(columns=['rightsHolder', 'datasetName'])
# for i in data['facet_counts']['facet_pivot']['rightsHolder,datasetName']:
#     c_group = i['value']
#     c_dataset = [ii['value']for ii in i['pivot']]
#     a = pd.DataFrame({'rightsHolder': c_group, 'datasetName': c_dataset})
#     final_d = pd.concat([final_d,a])
