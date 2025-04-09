import pandas as pd
import akshare as ak
import matplotlib.pyplot as plt
import seaborn as sns

from constants.file_path import HISTORY_FILE_PATH


# 绘制折线图
def show_line_chart(df, save_as_png=False, file_name="line_chart.png"):
    with plt.style.context({'font.sans-serif': ['SimHei'], 'axes.unicode_minus': False}):
        # 绘制折线图
        plt.figure(figsize=(12, 6))  # 设置图像大小
        plt.plot(df.index, df['累计净值'], label='策略累计净值', marker='o')  # 绘制累计净值折线图
        plt.plot(df.index, df['基准_等权指数_累计净值'], label='基准累计净值（等权指数）', marker='x')  # 绘制基准等权指数累计净值折线图

        # 添加图例
        plt.legend()

        # 添加标题和轴标签
        plt.title('策略与基准累计净值对比')
        plt.xlabel('日期')
        plt.ylabel('净值')

        # 格式化日期显示
        plt.gcf().autofmt_xdate()  # 自动旋转日期标签，避免重叠

        # 显示网格
        plt.grid(True)

        # 调整网格线密度
        plt.minorticks_off()  # 关闭次级刻度
        plt.grid(which='major', linestyle='--', linewidth=0.5, alpha=0.7)  # 设置主网格线样式

        # 显示图像
        plt.show()

        if save_as_png:
            plt.savefig(file_name, dpi=300, bbox_inches='tight')
            plt.close()


def show_table(df):
    # 绘制热力图
    plt.figure(figsize=(16, 12))  # 调整图片大小
    sns.heatmap(df, annot=True, fmt=".1f", cmap="coolwarm", linewidths=1.5)

    # 设置刻度标签的旋转角度
    plt.xticks(rotation=0)  # 横坐标标签水平显示
    plt.yticks(rotation=0)  # 纵坐标标签水平显示
    plt.show()


bond_df = pd.read_csv(HISTORY_FILE_PATH)
bond_df['日期'] = pd.to_datetime(bond_df['日期'])
bond_df = bond_df.dropna(subset=['收盘价', '转股溢价率', '信用评级'])
# 过滤低信用评级的可转债
# credit_level = ['CCC', 'CC', 'B-', 'B+', 'BB-', 'BB']
# bond_df = bond_df.query("信用评级 not in @credit_level")

start_date = pd.to_datetime('20180101')  # 数据开始日期
end_date = pd.to_datetime('20241231')  # 数据结束日期
data_df = bond_df[(bond_df['日期'] >= start_date) & (bond_df['日期'] <= end_date)]
data_df = data_df.sort_values(by=['日期', '债券代码'])

# 设置时间重采样聚合时的取值规则
agg_dict = {
    '收盘价': 'last',  # 月末按收盘价调仓，因此收盘价取月末值
    '转股溢价率': 'last',  # 根据月末的转股溢价率调仓，因此转股溢价率取月末值
    '债券简称': 'last',
}

# 重采样函数要求Index必须为datetime类型，因此将日期列转换为datetime格式
data_df = data_df.set_index('日期')
resample_df = data_df.groupby('债券代码').apply(lambda x: x.resample('1ME').agg(agg_dict), include_groups=False)
resample_df = resample_df.reset_index()  # 重置索引

# 使用 shift() 方法向上移动一行，将最后一行的月收益率赋值为0。取值含义为：如果该日持有该可转债，那么到下一个调仓日的收益率是多少
resample_df['月收益率'] = resample_df.groupby('债券代码')['收盘价'].pct_change().shift(-1).fillna(0)

resample_df['收盘价排名'] = resample_df.groupby('日期')['收盘价'].rank(ascending=False)
resample_df = resample_df.sort_values(by=['日期', '收盘价排名'])
# resample_df = resample_df[resample_df['债券简称'] == '海印转债']

# 每一期对所有个股进行排名，取前N名继续持有，其余清仓s
hold_df = resample_df[resample_df['收盘价排名'] <= 20].copy()

# 计算扣除交易成本后的月收益率
c_rate = 1 / 1000  # 交易费率
hold_df['月收益率'] = - c_rate + (1 + hold_df['月收益率']) * (1 - c_rate) - 1

# 计算整个组合的月收益率
results_df = hold_df.groupby('日期')[['月收益率']].mean()
results_df['累计净值'] = (results_df['月收益率'] + 1).cumprod()

# 获取可转债等权指数的数据
bench_mark = ak.bond_cb_index_jsl()[['price_dt', 'price']]
bench_mark['price_dt'] = pd.to_datetime(bench_mark['price_dt'])  # 将日期设为datetime格式
bench_mark = bench_mark.set_index('price_dt')  # 将日期设置为索引
base_price = bench_mark['price'].iloc[0]  # 获取基准价格

# 自动根据索引对齐数据，匹配不上索引的行用NaN填充
results_df['基准_等权指数_累计净值'] = bench_mark.resample('1ME').agg({'price': 'last'}) / base_price
results_df['基准_等权指数_月收益率'] = results_df['基准_等权指数_累计净值'].pct_change().fillna(0)

results_df['超额收益'] = results_df['累计净值'] / results_df['基准_等权指数_累计净值']
results_df.index = results_df.index.strftime('%Y-%m-%d')

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', 1000)  # 调整控制台显示宽度

show_line_chart(results_df)
