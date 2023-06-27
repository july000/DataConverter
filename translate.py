import pandas as pd
import configparser
import sys
import math
import pymap3d
import json
import argparse

def load_json(input_file):
    with open(input_file) as f:
        return json.load(f)

def read_config_file(config_file):
    config = configparser.ConfigParser(allow_no_value=True)
    # case-sensitive when read from config file
    config.optionxform = str
    try:
        config.read(config_file, encoding='utf-8')
        file_type = config['FileType']
        json_param = config['Json']
        constant = config.items('Const')
        column_settings = config.items('ColumnSettings')
        series_conversion_rules = config.items('SeriesRules')
        dataframe_conversion_rules = config.items('DataframeRules')
        return dict(file_type), dict(json_param), dict(constant), dict(column_settings), dict(series_conversion_rules), dict(dataframe_conversion_rules)
    except Exception as e:
        print(f"Error in reading config file: {e}")
        sys.exit()

def read_file(file_type, json_param, input_file):
    try:
        if file_type['type'] == 'csv':
            df = pd.read_csv(input_file)
        elif file_type['type'] == 'excel':
            df = pd.read_excel(input_file)
        elif file_type['type'] == 'txt':
            df = pd.read_csv(input_file, sep="\s+")
        elif file_type['type'] == 'json':
            json_data = load_json(input_file)
            df = pd.json_normalize(json_data, record_path=eval(json_param['record_path']), meta=eval(json_param['metadata']))
        return df
    except Exception as e:
        print(f"Error in reading {file_type} file: {e}")
        sys.exit()

# 根据指定的列名和转换规则，转换 DataFrame，并生成转换后的 CSV 文件
def process_data_frame(df, constant, column_settings, series_conversion_rules, dataframe_conversion_rules):
    # 根据指定的列名，选择 DataFrame 的列
    src_column_names = list(set(name for name in list(column_settings.values()) if name != 'None'))
    df = df[src_column_names]
    dst_df = pd.DataFrame(columns=list(column_settings.keys()))

    # 设计到一列的转换规则
    for dst_column_name, series_rule in series_conversion_rules.items():
        dst_column_name = dst_column_name.strip()
        src_column_name = column_settings[dst_column_name]
        dst_df[dst_column_name] = df[src_column_name].apply(eval(series_rule))
    
    # 涉及到多列的使用
    for dst_column_name, df_rule in dataframe_conversion_rules.items():
        dst_column_name = dst_column_name.strip().split(', ')
        if len(dst_column_name) <= 1:
            dst_column_name = dst_column_name[0]
            dst_df[dst_column_name] = df.apply((eval(df_rule)), axis=1)
        else:
            dst_df[dst_column_name] = pd.DataFrame(list(df.apply((eval(df_rule.replace('${Const:', '{').format(**constant))), axis=1)), columns=dst_column_name)
    
    # generated_df = generated_df.assign(**{col: df.apply(eval(rule), axis=1) for col, rule in dataframe_conversion_rules.items()})
    
    # 设置常数列
    # for const_column_name, value in constant.items():
    #     if const_column_name in list(column_settings.keys()):
    #         generated_df[const_column_name] = eval(value)
    return dst_df

# 生成 CSV 文件，输出转换后的数据
def write_csv_file(output_file, df):
    try:
        df.to_csv(output_file, index=False)
        print(f"CSV file : '{output_file}' has been generated successfully!")
    except Exception as e:
        print(f"Error in generating CSV file: {e}")
        sys.exit()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config-file', dest='config_file', default='F:\\renjunmei007\\05_code\\github\\DataConverter\\config.ini')
    parser.add_argument('--input-file', dest='input_file', default='F:\\renjunmei007\\05_code\\github\\DataConverter\\sample_case\\offset_flatten_rsm_30_all.csv')
    parser.add_argument('--output-file', dest='output_file', default='F:\\renjunmei007\\05_code\\github\\DataConverter\\output.csv')
    args = parser.parse_args()

    file_type, json_param, constant, column_settings, series_conversion_rules, dataframe_conversion_rules = read_config_file(args.config_file)
    src_df = read_file(file_type, json_param, args.input_file)
    dst_df = process_data_frame(src_df, constant, column_settings, series_conversion_rules, dataframe_conversion_rules)
    write_csv_file(args.output_file, dst_df)