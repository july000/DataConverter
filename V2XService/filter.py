import pymongo
import datetime
import json
import pandas as pd
import math
from gps_encoding import wgs84_to_gcj02
import pymap3d

COLUMN_NAME = ['ID','Time','PositionX','PositionY','PositionZ','Length','Width','Height','Yaw','Pitch','Roll',
                'VX','VY','VZ','AX','AY','AZ','Category','Style','Color','Ego']
CATEGORY_MAP0 = {1:"小车", 2:"货车", 3:"机动车", 4:"非机动车", 5:"行人", 6:"二轮车", 7:"三轮车", 8:"公交车", 9:"大巴(货车)"}

CATEGORY_MAP1 = {1:"car", 2:"truck", 3:"机动车", 4:"非机动车", 5:"man", 6:"normal", 7:"tricycle", 8:"coach", 9:"van_truck"}
CATEGORY_MAP2 = {1:"vehicle", 2:"vehicle", 3:"机动车", 4:"非机动车", 5:"pedestrian", 6:"bike", 7:"vehicle", 8:"vehicle", 9:"vehicle"}
STYLE_MAP = {"car":"vehicle", "mixed_truck":"vehicle", "truck":"vehicle", "coach":"vehicle", "van_truck":"vehicle", "tricycle":"vehicle", "motor":"vehicle",
                 "electric":"bike", "normal":"bike",
                 "man":"pedestrian", "woman":"pedestrian", "child":"pedestrian",
                 "dog":"animal",
                 "unknown": "unknown"
                }
COLOR_MAP = {0:'white',1:'gray',3:'yellow',4:'pink',5:'purple',6:'green',7:'blue',8:'red',9:'brown',10:'orange',11:'black'}

client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["RSM"]

def filter_files(rsu_id, start_time, end_time):
    collection = db[rsu_id]
    query = {'data.timestamp': {'$gte': start_time, '$lte': end_time}}
    count = collection.count_documents(query)
    result = collection.find(query)
    if count == 0:
        print("No files matching the filter criteria were found")
        return None
    else:
        return list(result)

def convert_files(files, output_file):
    if files is None:
        return
    data_frames = (pd.json_normalize(file,
                record_path=['data', 'rsms', 'participants'],
                meta=[['data', 'timestamp'], ['data', 'rsms', 'refPos', 'lon'], ['data', 'rsms', 'refPos', 'lat']]
            ) for file in files)
    df = pd.concat(data_frames, ignore_index=True)
    df.sort_values(by=['data.timestamp'], inplace=True)

    origin_gps_point = [23.023899623618, 113.488177461743, 0.0]
    df.loc[:,'pos.lon'], df.loc[:,'pos.lat'] = zip(*df.apply(lambda x: wgs84_to_gcj02(x['pos.lon'], x['pos.lat']), axis=1))
    # df.loc[:,'EgoPositionX'], df.loc[:,'EgoPositionY'], df.loc[:,'EgoPositionZ'] = zip(*df.apply(lambda x: pymap3d.geodetic2enu(x['data.rsms.refPos.lon'], x['data.rsms.refPos.lat'], 0.0, origin_gps_point[0], origin_gps_point[1], 0.0), axis=1))
    df.loc[:,'PositionX'], df.loc[:,'PositionY'], df.loc[:,'PositionZ'] = zip(*df.apply(lambda x: pymap3d.geodetic2enu(x['pos.lat'], x['pos.lon'], 0.0, origin_gps_point[0], origin_gps_point[1], 0.0), axis=1))

    df['data.timestamp'] = df['data.timestamp'] / 1000
    df['size.length'] = df['size.length'] / 100
    df['size.width'] = df['size.width'] / 100
    df['size.height'] = df['size.height'] / 100
    # df['heading'] = (90.0 - df['heading'] * 0.0125) % 360.0
    df['heading'] = df['heading'] * 0.0125
    df['speed'] = df['speed'] * 0.02

    df['ptcType'] = df['ptcType'].replace(CATEGORY_MAP2)
    df['Style'] = df['ptcType'].replace(CATEGORY_MAP2)
    # df['ptcType'] = 'vehicle'
    # df['Style'] = 'car'

    df['vehicleColor'] = df['vehicleColor'].replace(COLOR_MAP)
    df['VX'] = df.apply(lambda row: row['speed'] * math.cos(math.radians(row['heading'])), axis=1)
    df['VY'] = df.apply(lambda row: row['speed'] * math.sin(math.radians(row['heading'])), axis=1)
    df['VZ'] = 0.0
    df['AX'] = 0.0
    df['AY'] = 0.0
    df['AZ'] = 0.0

    df['Pitch'] = 0.0
    df['Roll'] = 0.0
    df['Ego'] = 'N'

    df.rename(columns = {'data.timestamp':'Time', 
                        'ptcId':'ID', 
                        'ptcType':'Category', 
                        'size.length':'Length', 'size.width':'Width', 'size.height':'Height',
                        'vehicleColor':'Color',
                        'heading':'Yaw'
                        }, inplace = True)
    
    df_sub = df[COLUMN_NAME]
    df_sub.sort_values(by=['ID', 'Time'], inplace=True)
    df_sub.to_csv(output_file, index=False)


if __name__ == '__main__':
    rsu_id = "440113GXX000200000006"
    start_time = 1689143775000
    end_time = 1689143777000
    files = filter_files(rsu_id, start_time, end_time)
    output_file = "F:\\renjunmei007\\05_code\\github\\DataConverter\\V2XService\\rsm.csv"
    convert_files(files, output_file)
