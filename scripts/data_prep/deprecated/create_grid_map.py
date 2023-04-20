import numpy as np
import bisect

# x: longtitude, y: latitude

# grid = [0.01, 0.05, 0.1, 1]

def convert_grid_to_coor(grid_x, grid_y, grid):
    list_x = np.arange(-180, 180, grid)
    list_y = np.arange(-90, 90, grid)
    center_x = (list_x[grid_x] + list_x[grid_x+1])/2
    center_y = (list_y[grid_y] + list_y[grid_y+1])/2
    return center_x, center_y

# x_grid = bisect.bisect(list_x, grid_x)-1
# y_grid = bisect.bisect_right(list_y, grid_y)-1

def convert_coor_to_grid(x, y, grid):
    list_x = np.arange(-180, 180, grid)
    list_y = np.arange(-90, 90, grid)
    grid_x = bisect.bisect(list_x, x)-1
    grid_y = bisect.bisect(list_y, y)-1
    return grid_x, grid_y

# update current csv
import pandas as pd
import os
import glob

read_path = '/tbia-volumes/solr/csvs/posted_csv/'
save_path = '/tbia-volumes/solr/csvs/update/'
extension = 'csv'
file_list = glob.glob('{}*.{}'.format(read_path,extension))

# 用csv更新速度會快很多

for j in file_list:
    print(j)
    df = pd.read_csv(j)
    df['grid_x_1'] = -1
    df['grid_y_1'] = -1
    df['grid_x_5'] = -1
    df['grid_y_5'] = -1
    df['grid_x_10'] = -1
    df['grid_y_10'] = -1
    df['grid_x_100'] = -1
    df['grid_y_100'] = -1
    # for i in range(len(df)):
    for i in range(len(df)):
        # print(i)
        if not pd.isna(df.iloc[i].standardLatitude) and not pd.isna(df.iloc[i].standardLongitude):
            grid_x, grid_y = convert_coor_to_grid(df.iloc[i].standardLongitude, df.iloc[i].standardLatitude, 0.01)
            df.iloc[i, df.columns.get_loc('grid_x_1')] = grid_x
            df.iloc[i, df.columns.get_loc('grid_y_1')] = grid_y
            grid_x, grid_y = convert_coor_to_grid(df.iloc[i].standardLongitude, df.iloc[i].standardLatitude, 0.05)
            df.iloc[i, df.columns.get_loc('grid_x_5')] = grid_x
            df.iloc[i, df.columns.get_loc('grid_y_5')] = grid_y
            grid_x, grid_y = convert_coor_to_grid(df.iloc[i].standardLongitude, df.iloc[i].standardLatitude, 0.1)
            df.iloc[i, df.columns.get_loc('grid_x_10')] = grid_x
            df.iloc[i, df.columns.get_loc('grid_y_10')] = grid_y
            grid_x, grid_y = convert_coor_to_grid(df.iloc[i].standardLongitude, df.iloc[i].standardLatitude, 1)
            df.iloc[i, df.columns.get_loc('grid_x_100')] = grid_x
            df.iloc[i, df.columns.get_loc('grid_y_100')] = grid_y
    # df = df.drop(columns=['location_rpt'])
    f_name = j.split('.')[0].split('/')[-1]
    df = df.replace({np.nan: None})
    df.to_csv(f'{save_path}{f_name}_grid.csv',index=False)


# row = df.iloc[i]

# class NpEncoder(json.JSONEncoder):
#     def default(self, obj):
#         if isinstance(obj, np.integer):
#             return int(obj)
#         if isinstance(obj, np.floating):
#             return float(obj)
#         if isinstance(obj, np.ndarray):
#             return obj.tolist()
#         return super(NpEncoder, self).default(obj)



# data = []

# for i in range(3):
#     row = df.iloc[i]
#     c = {'id': row.id, 'grid_x': {'set': row.grid_x}, 'grid_y': {'set': row.grid_y}}
#     data += [c]