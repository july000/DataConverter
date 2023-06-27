import pandas as pd
import configparser
import sys
import math
import pymap3d

def read_config_file(config_file):
    config = configparser.ConfigParser()
    # case-sensitive when read from config file
    config.optionxform = str
    try:
        config.read(config_file)
        constant = config.items('Const')
        column_settings = config.items('ColumnSettings')
        series_conversion_rules = config.items('SeriesRules')
        dataframe_conversion_rules = config.items('DataframeRules')
        return dict(constant), dict(column_settings), dict(series_conversion_rules), dict(dataframe_conversion_rules)
    except Exception as e:
        print(f"Error in reading config file: {e}")
        sys.exit()

def read_csv_file(input_file):
    try:
        df = pd.read_csv(input_file)
        return df
    except Exception as e:
        print(f"Error in reading CSV file: {e}")
        sys.exit()

# 根据指定的列名和转换规则，转换 DataFrame，并生成转换后的 CSV 文件
def process_data_frame(df, constant, column_settings, series_conversion_rules, dataframe_conversion_rules):
    # 根据指定的列名，选择 DataFrame 的列
    src_column_names = list(set(name for name in list(column_settings.values()) if name != 'None'))
    df = df[src_column_names]
    generated_df = pd.DataFrame(columns=list(column_settings.keys()))

    # 设计到一列的转换规则
    for dst_column_name, series_rule in series_conversion_rules.items():
        dst_column_name = dst_column_name.strip()
        src_column_name = column_settings[dst_column_name]
        generated_df[dst_column_name] = df[src_column_name].apply(eval(series_rule))
    
    # 涉及到多列的使用
    for dst_column_name, df_rule in dataframe_conversion_rules.items():
        dst_column_name = dst_column_name.strip().split(', ')
        if len(dst_column_name) <= 1:
            dst_column_name = dst_column_name[0]
            generated_df[dst_column_name] = df.apply((eval(df_rule)), axis=1)
        else:
            generated_df[dst_column_name] = pd.DataFrame(list(df.apply((eval(df_rule.replace('${Const:', '{').format(**constant))), axis=1)), columns=dst_column_name)
    
    # generated_df = generated_df.assign(**{col: df.apply(eval(rule), axis=1) for col, rule in dataframe_conversion_rules.items()})
    
    # 设置常数列
    # for const_column_name, value in constant.items():
    #     if const_column_name in list(column_settings.keys()):
    #         generated_df[const_column_name] = eval(value)
    return generated_df

# 生成 CSV 文件，输出转换后的数据
def write_csv_file(output_file, df):
    try:
        df.to_csv(output_file, index=False)
        print(f"CSV file : '{output_file}' has been generated successfully!")
    except Exception as e:
        print(f"Error in generating CSV file: {e}")
        sys.exit()

if __name__ == '__main__':
    config_file = 'config.ini'
    constant, column_settings, series_conversion_rules, dataframe_conversion_rules = read_config_file(config_file)

    input_file = 'offset_flatten_rsm_30_all.csv'
    df = read_csv_file(input_file)

    # 根据列名和转换规则进行 DataFrame 转换
    generated_df = process_data_frame(df, constant, column_settings, series_conversion_rules, dataframe_conversion_rules)

    # 生成转换后的 CSV 文件
    output_file = 'output.csv'
    write_csv_file(output_file, generated_df)