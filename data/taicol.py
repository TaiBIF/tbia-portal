import pandas as pd
import numpy as np


taicol = pd.read_csv('/tbia-volumes/bucket/TaiwanSpecies20211019_UTF8.csv')
# taicol = pd.read_csv('/Users/taibif/Documents/GitHub/tbia-volumes/TaiwanSpecies20210618_UTF8.csv')
taicol = taicol[taicol['is_accepted_name']==True][['name','common_name_c']]
taicol = taicol.replace({np.nan: ''})
taicol['common_name_c'] = taicol['common_name_c'].apply(lambda x: x.split(';')[0] if x else x)

