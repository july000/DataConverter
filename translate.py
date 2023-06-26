from lib2to3.pgen2.literals import evalString
import pandas as pd
import configparser
import sys

def read_config_file(config_file):
    config = configparser.ConfigParser()
    try:
        config.read(config_file)
        column_settings = config.items('ColumnSettings')
        conversion_rules = config.items('ConversionRules')
        return dict(column_settings), dict(conversion_rules)
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
def process_data_frame(df, column_settings, conversion_rules):
    # 根据指定的列名，选择 DataFrame 的列
    column_names = [name for name in list(column_settings.values()) if name != 'None']
    # column_names = [column_settings[key] for key in column_settings]
    df = df[column_names]

    # 根据转换规则，对 DataFrame 进行转换
    for columns, rule in conversion_rules.items():
        
        # columns, convert_func = rule.split(':')  # 从规则中解析出要转换的列和转换函数
        src_columns = column_settings[columns.strip()].split('_')[0]  # 解析出要转换的源列和目标列, split返回的是一个list，如果不加【0】，用df[src_columns]的type是dataframe
        # src_column_name, dst_column_name = [col.strip() for col in src_columns]
        dst_column_name = columns.strip().split('_')[0]
        df[dst_column_name] = df[src_columns].apply(eval(rule))

    return df

# 生成 CSV 文件，输出转换后的数据
def write_csv_file(output_file, df):
    try:
        df.to_csv(output_file, index=False)
        print(f"CSV file '{output_file}' has been generated successfully!")
    except Exception as e:
        print(f"Error in generating CSV file: {e}")
        sys.exit()

if __name__ == '__main__':
    config_file = 'F:\\renjunmei007\\05_code\\back\\51World\\TrajectoryProcess\\internal\\desay\\config.ini'
    column_settings, conversion_rules = read_config_file(config_file)

    # input_file = 'F:\\renjunmei007\\05_code\\back\\51World\\TrajectoryProcess\\internal\\desay\\input.csv'
    input_file = 'G:\\CyTrafficEditor\\CyTraffic\\data\\test_cases\\zhilian\\offset_flatten_rsm_30_all.csv'
    df = read_csv_file(input_file)

    # 根据列名和转换规则进行 DataFrame 转换
    df = process_data_frame(df, column_settings, conversion_rules)

    # 生成转换后的 CSV 文件
    output_file = 'F:\\renjunmei007\\05_code\\back\\51World\\TrajectoryProcess\\internal\\desay\\output.csv'
    write_csv_file(output_file, df)