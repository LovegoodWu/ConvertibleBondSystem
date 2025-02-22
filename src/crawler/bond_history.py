import os
import tqdm
from os.path import abspath, dirname

import pandas as pd
import akshare as ak

PROJECT_ROOT_PATH = dirname(dirname(dirname(abspath(__file__))))
HISTORY_FILE_DIRECTORY = os.path.join(PROJECT_ROOT_PATH, "data/history")

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', 1000)  # 调整控制台显示宽度


def download_bond_data(to_file_path):
    data_list = []
    c_bond_df = ak.bond_zh_cov()

    # 测试时可以先只获取部分数据
    # c_bond_df = c_bond_df[c_bond_df['债券代码'] == '123238']
    # c_bond_df = c_bond_df.tail(100)
    # c_bond_df = c_bond_df.iloc[100:201]

    # 指定要过滤掉的可转债的债券简称
    no_valid_data_bond_names = ['07日照债', '09长虹债', '08江铜债', '08葛洲债', '08宝钢债', '08康美债', '08国电债',
                                '08青啤债', '08上港债', '08石化债', '中兴债1', '08中远债', '08赣粤债', '08上汽债',
                                '07深高债']
    c_bond_df = c_bond_df.query("债券简称 not in @no_valid_data_bond_names")
    # c_bond_df = c_bond_df[~c_bond_df['债券简称'].isin(no_valid_data_names)]

    for index, row in tqdm.tqdm(c_bond_df.iterrows(), desc="获取可转债历史行情", total=len(c_bond_df)):
        code = row['债券代码']
        name = row['债券简称']
        publish_date = row['上市时间']
        j = 1
        while True:
            try:
                data = ak.bond_zh_cov_value_analysis(symbol=code)  # 逐个获取可转债数据
                # 剔除上市时间之前的数据
                data = data[data['日期'] >= publish_date]

                # 拼接部分可转债基础数据
                # columns_to_add = ['债券代码', '债券简称']
                # row_selected = row[columns_to_add]
                # data = data.assign(**row_selected)

                data['债券代码'] = code
                data_list.append(data)  # 将每只可转债的数据添加到data_list
                break
            except:  # 如遇出错则重试3次
                print("第{}次重试获取{}的数据\n".format(j, name))
                j += 1
                if j > 3:
                    break

    data_df = pd.concat(data_list)

    # 拼接部分可转债基础数据
    data_df = pd.merge(
        data_df,
        c_bond_df[['债券代码', '债券简称', '正股代码', '正股简称', '上市时间', '信用评级']],
        on='债券代码'
    )

    # 校验数据质量
    check_df(data_df, False)

    data_df.to_csv(to_file_path, index=False, encoding="utf-8")


def check_df(df, do_clean):
    print("数据总行数：{}".format(len(df)))

    # 查找所有包含空值的行
    # null_rows = df[df.isna().any(axis=1)]

    null_rows = df[df['收盘价'].isna()]

    # 打印结果
    print("包含空值的行：")
    print(null_rows.to_string(index=False))

    # 附加统计信息（可选）
    print("\n空值统计：")
    print(df.isna().sum())

    if do_clean:
        df.dropna(subset=['收盘价'], how='all', inplace=True)
        df.dropna(subset=['纯债价值', '转股价值', '纯债溢价率', '转股溢价率'],
                  how='all', inplace=True)
        print("数据清洗后总行数：{}".format(len(df)))


download_bond_data(os.path.join(HISTORY_FILE_DIRECTORY, "history_akshare.csv"))
