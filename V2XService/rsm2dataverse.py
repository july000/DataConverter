import pandas as pd
import pymap3d
import numpy as np
import json
import os
from pathlib import Path
import math
from gps_encoding import wgs84_to_gcj02

def load_json(input_file):
    with open(input_file) as f:
        return json.load(f)

def load_json_wrapper(file_path):
    return load_json(str(file_path))



COLUMN_NAME = ['ID','Time','PositionX','PositionY','PositionZ','Length','Width','Height','Yaw','Pitch','Roll',
                'VX','VY','VZ','AX','AY','AZ','Category','Style','Color','Ego']
CATEGORY_MAP = {0:'unkown', 1:'motor', 2:'non-motor', 3:'pedestrian', 4:'rsu'}
STYLE_MAP = {"car":"vehicle", "mixed_truck":"vehicle", "truck":"vehicle", "coach":"vehicle", "van_truck":"vehicle", "motor":"vehicle",
                 "electric":"bike", "normal":"bike",
                 "man":"pedestrian", "woman":"pedestrian", "child":"pedestrian",
                 "dog":"animal",
                 "unknown": "unknown"
                }
COLOR_MAP = {0:'white',1:'gray',3:'yellow',4:'pink',5:'purple',6:'green',7:'blue',8:'red',9:'brown',10:'orange',11:'black'}

def run(input_dir, output_file):
    file_paths = list(Path(input_dir).glob('*.json'))

    data_frames = (pd.json_normalize(
                    load_json_wrapper(file_path),
                    record_path=['data', 'rsms', 'participants'],
                    meta=[['data', 'timestamp'], ['data', 'rsms', 'refPos', 'lon'], ['data', 'rsms', 'refPos', 'lat']]
                ) for file_path in file_paths)

    df = pd.concat(data_frames, ignore_index=True)
    df.sort_values(by=['data.timestamp'], inplace=True)
    df.to_csv(output_file.split('.csv')[0]+"_all.csv", index=False)


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
    # df['ptcType'] = df['ptcType'].replace(CATEGORY_MAP)
    # df['Style'] = df['ptcType'].replace(STYLE_MAP)
    df['ptcType'] = 'vehicle'
    df['Style'] = 'car'
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
    df_sub.to_csv(output_file, index=False)
    
    # df.to_csv(output_file.split('.csv')[0]+"_all.csv", index=False)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--input-dir', dest='input_dir', default='F:\\renjunmei007\\05_code\\github\\gicc-rawdata-dump\\dump\\202306291800')
    parser.add_argument('--output-file', dest='output_file', default='F:\\renjunmei007\\05_code\\github\\gicc-rawdata-dump\\output\\202306291800\\rsm.csv')
    args = parser.parse_args()

    run(args.input_dir, args.output_file)
