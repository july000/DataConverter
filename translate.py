import pandas as pd
import configparser
import sys
import math
import pymap3d
import json
import argparse
import bisect
import numpy as np
from gps_encoding import wgs84_to_gcj02


def load_json(input_file):
  with open(input_file) as f:
      return json.load(f)

def set_unchange_cols_value(column_settings, ego_series_conversion_rules, common_series_conversion_rules, dst_df, src_df):
    unchange_cols = list(set(column_settings.keys()) - set(ego_series_conversion_rules) - set(common_series_conversion_rules))
    for col in unchange_cols:
      if column_settings[col] == 'None':
        continue
      dst_df[col] = src_df[column_settings[col]]
    return dst_df

class ConfigData:
  def __init__(self):
    self.file_type = {}
    self.json_param = {}
    self.constant = {}
    self.column_settings = {}
    self.ego_column_settings = {}
    self.obj_column_settings = {}
    self.series_conversion_rules = {}
    self.ego_series_conversion_rules = {}
    self.obj_series_conversion_rules = {}
    self.dataframe_conversion_rules = {}
    self.relative_position = False
    self.encrypted = False
    self.gps = False
    self.ego_file = None
    self.obj_file = None
    self.input_file = None
    self.output_file = None

  def read_config_file(self, config_file):
    config = configparser.ConfigParser(allow_no_value=True)
    # case-sensitive when read from config file
    config.optionxform = str
    try:
      config.read(config_file, encoding='utf-8')
      self.file_type = dict(config['FileType'])
      self.json_param = dict(config['Json'])
      self.constant = dict(config.items('Const'))
      self.series_conversion_rules = dict(config.items('CommonSeriesRules'))
      self.dataframe_conversion_rules = dict(config.items('CommorMultiSeriesRules'))
      self.relative_position = config.getboolean('Position', 'relative_position')
      self.encrypted = config.getboolean('Security', 'encrypted')
      self.gps = config.getboolean('Const', 'GPS')
      if self.gps:
        self.originLat = config.get('Const', 'OriginLat')
        self.originLon = config.get('Const', 'OriginLon')

      if self.relative_position:
        self.ego_file = config.get('Position', 'ego_file')
        self.obj_file = config.get('Position', 'obj_file')
        self.ego_column_settings = dict(config.items('EgoColumnSettings'))
        self.obj_column_settings = dict(config.items('ObjColumnSettings'))
        self.ego_series_conversion_rules = dict(config.items('EgoSeriesRules'))
        self.obj_series_conversion_rules = dict(config.items('ObjSeriesRules'))
      else:
        self.input_file = config.get('General', 'input_file')
        self.column_settings = dict(config.items('ColumnSettings'))
      self.output_file = config.get('General', 'output_file')
      # return config
    except Exception as e:
      print(f"Error in reading config file: {e}")
      sys.exit()

def read_file(file_type, json_param, relative_position=False, input_file=None, ego_file=None, obj_file=None):
  try:
    if relative_position:
      if file_type['type'] == 'csv':
        ego_df = pd.read_csv(ego_file)
        obj_df = pd.read_csv(obj_file)
      elif file_type['type'] == 'excel':
        ego_df = pd.read_excel(ego_file)
        obj_df = pd.read_excel(obj_file)
      elif file_type['type'] == 'txt':
        ego_df = pd.read_csv(ego_file, sep = "\s+")
        obj_df = pd.read_csv(obj_file, sep = "\s+")
      return ego_df, obj_df
    else:
      if file_type['type'] == 'csv':
        df = pd.read_csv(input_file)
      elif file_type['type'] == 'excel':
        df = pd.read_excel(input_file)
      elif file_type['type'] == 'txt':
        df = pd.read_csv(input_file, sep="\s+")
      elif file_type['type'] == 'json':
        json_data = load_json(input_file)
        df = pd.json_normalize(json_data, record_path=eval(json_param['record_path']), meta=eval(json_param['metadata']))
      return df, None
  except Exception as e:
    print(f"Error in reading {file_type} file: {e}")
    sys.exit()

# 根据指定的列名和转换规则，转换 DataFrame，并生成转换后的 CSV 文件
def process_data_frame(df, constant, column_settings, series_conversion_rules, dataframe_conversion_rules, ego_series_conversion_rules = None, obj_series_conversion_rules = None):
  # 根据指定的列名，选择 DataFrame 的列
  src_column_names = list(set(name for name in list(column_settings.values()) if name != 'None'))
  df = df[src_column_names]
  dst_df = pd.DataFrame(columns=list(column_settings.keys()))

  # 涉及到一列的转换规则
  for dst_column_name, series_rule in series_conversion_rules.items():
    dst_column_name = dst_column_name.strip()
    src_column_name = column_settings[dst_column_name]
    dst_df[dst_column_name] = df[src_column_name].apply(eval(series_rule))

  if ego_series_conversion_rules is not None:
    for dst_column_name, ego_series_rule in ego_series_conversion_rules.items():
      dst_column_name = dst_column_name.strip()
      src_column_name = column_settings[dst_column_name]
      dst_df[dst_column_name] = df[src_column_name].apply(eval(ego_series_rule))
    dst_df = set_unchange_cols_value(column_settings, ego_series_conversion_rules.keys(), series_conversion_rules.keys(), dst_df, df)

  if obj_series_conversion_rules is not None:
    for dst_column_name, obj_series_rule in obj_series_conversion_rules.items():
      dst_column_name = dst_column_name.strip()
      src_column_name = column_settings[dst_column_name]
      dst_df[dst_column_name] = df[src_column_name].apply(eval(obj_series_rule))
    dst_df = set_unchange_cols_value(column_settings, obj_series_conversion_rules.keys(), series_conversion_rules.keys(), dst_df, df)


  # 涉及到多列的使用
  for dst_column_name, df_rule in dataframe_conversion_rules.items():
    dst_column_name = dst_column_name.strip().split(', ')
    if len(dst_column_name) <= 1:
      dst_column_name = dst_column_name[0]
      dst_df[dst_column_name] = df.apply((eval(df_rule)), axis=1)
    else:
      dst_df[dst_column_name] = pd.DataFrame(list(df.apply((eval(df_rule.replace('${Const:', '{').format(**constant))), axis=1)), columns=dst_column_name)
  
  dst_df = set_unchange_cols_value(column_settings, dataframe_conversion_rules.keys(), series_conversion_rules.keys(), dst_df, df)
  return dst_df

def ref_to_global(yaw, px, py, rx, ry, ryaw):
  main_yaw = math.radians(yaw)
  obj_ryaw = math.radians(ryaw)

  x_axis = np.array([math.cos(main_yaw), math.sin(main_yaw)])
  y_axis = np.array([-math.sin(main_yaw), math.cos(main_yaw)])
  point_in_enu = np.array([px, py]) + x_axis * rx + y_axis * ry
  obj_yaw_vec = x_axis * math.cos(obj_ryaw) + y_axis * math.sin(obj_ryaw)
  obj_yaw = math.degrees(math.atan2(obj_yaw_vec[1], obj_yaw_vec[0]))
  return point_in_enu[0], point_in_enu[1], obj_yaw

def interpolate(ego_df, all_times, time, rx, ry,ryaw):
  n = len(all_times)
  idx = bisect.bisect_left(all_times, time, lo=1, hi=n-1)
  ego_prev_row = ego_df.iloc[idx-1]
  ego_next_row = ego_df.iloc[idx]
  a = (time-ego_prev_row.Time)/(ego_next_row.Time-ego_prev_row.Time)
  px = (1-a)*ego_prev_row.PositionX + a*ego_next_row.PositionX
  py = (1-a)*ego_prev_row.PositionY + a*ego_next_row.PositionY
  yaw = (1-a)*ego_prev_row.Yaw + a*ego_next_row.Yaw
  gx, gy, gyaw = ref_to_global(yaw, px, py, rx, ry, ryaw)
  return gx, gy, gyaw

def flat(ego_df, obj_df):
  if config.gps and config.encrypted:
    ego_df.loc[:,'PositionY'], ego_df.loc[:,'PositionX'] = zip(*ego_df.apply(lambda x: wgs84_to_gcj02(x['PositionY'], x['PositionX']), axis=1))
    ego_df.loc[:,'PositionX'], ego_df.loc[:,'PositionY'], ego_df.loc[:,'PositionZ'] = zip(*ego_df.apply(lambda x: pymap3d.geodetic2enu(x['PositionX'], x['PositionY'], 0.0, float(config.originLat), float(config.originLon), 0.0), axis=1))
  elif config.gps:
    ego_df.loc[:,'PositionX'], ego_df.loc[:,'PositionY'], ego_df.loc[:,'PositionZ'] = zip(*ego_df.apply(lambda x: pymap3d.geodetic2enu(x['PositionX'], x['PositionY'], 0.0, config.originLat, config.originLon, 0.0), axis=1))
  else:
    pass
  if obj_df is not None:
    obj_df.loc[:, 'PositionX'], obj_df.loc[:, 'PositionY'], obj_df.loc[:, 'Yaw'] = zip(*obj_df.apply(lambda x:interpolate(ego_df, ego_df['Time'], x.Time, x.PositionX, x.PositionY, x.Yaw), axis=1))
  new_df = pd.concat([ego_df, obj_df])
  return new_df

def write_csv_file(output_file, df):
  try:
    df.to_csv(output_file, index=False)
    print(f"CSV file : '{output_file}' has been generated successfully!")
  except Exception as e:
    print(f"Error in generating CSV file: {e}")
    sys.exit()

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('--config-file', dest='config_file', default='.\\config.ini')
  # parser.add_argument('--input-file', dest='input_file', default='F:\\renjunmei007\\05_code\\github\\DataConverter\\sample_case\\offset_flatten_rsm_30_all.csv')
  # parser.add_argument('--output-file', dest='output_file', default='F:\\renjunmei007\\05_code\\github\\DataConverter\\output.csv')
  args = parser.parse_args()
  config = ConfigData()
  config.read_config_file(args.config_file)

  #读取一个合并后的文件
  if not config.relative_position:
    src_df, _ = read_file(config.file_type, config.json_param, False, config.input_file)
    dst_df = process_data_frame(src_df, config.constant, config.column_settings, config.series_conversion_rules, config.dataframe_conversion_rules)
    new_df = flat(dst_df, None)
    write_csv_file(config.output_file, new_df)

  # 读取主车和对手车分开的两个文件
  # 读取相对位置文件
  else:
    ego_df, obj_df = read_file(config.file_type, config.json_param, relative_position=True, ego_file=config.ego_file, obj_file=config.obj_file)
    dst_ego_df = process_data_frame(ego_df, config.constant, config.ego_column_settings, config.series_conversion_rules, config.dataframe_conversion_rules, ego_series_conversion_rules = config.ego_series_conversion_rules, obj_series_conversion_rules = None)
    dst_obj_df = process_data_frame(obj_df, config.constant, config.obj_column_settings, config.series_conversion_rules, config.dataframe_conversion_rules, ego_series_conversion_rules = None, obj_series_conversion_rules = config.obj_series_conversion_rules)
    concat_df = flat(dst_ego_df, dst_obj_df)
    write_csv_file(config.output_file, concat_df)

