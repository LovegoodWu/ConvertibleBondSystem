from datetime import datetime

import backtrader as bt
import pandas as pd

from constants.file_path import HISTORY_FILE_PATH


# Create a Strategy
class TestStrategy(bt.Strategy):

    def log(self, txt, dt=None):
        """ 提供记录功能"""
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # 引用到输入数据的close价格
        self.dataclose = self.datas[0].close

    def next(self):
        # 目前的策略就是简单显示下收盘价。
        self.log('Close, %.2f' % self.dataclose[0])


if __name__ == '__main__':
    cerebro = bt.Cerebro()
    cerebro.addstrategy(TestStrategy)

    # 获取数据
    bond_df = pd.read_csv(HISTORY_FILE_PATH, encoding='GBK')
    print(bond_df.dtypes)
    bond_df['date'] = pd.to_datetime(bond_df['date'])
    bond_df['open'] = bond_df['close']
    bond_df['low'] = bond_df['close']
    bond_df['high'] = bond_df['close']
    bond_df = bond_df.sort_values(by=['date', 'bond_code'], ascending=[True, True])
    bond_df = bond_df[(bond_df['bond_code'] == 113070)]

    start_date = datetime(2025, 2, 1)  # 回测开始时间
    end_date = datetime(2025, 2, 28)  # 回测结束时间
    data = bt.feeds.PandasData(
        dataname=bond_df,
        fromdate=start_date,
        todate=end_date,
        datetime='date',
        open='open',
        high='high',
        low='low',
        close='close',
        volume=-1,
        openinterest=-1)  # 加载数据

    cerebro.adddata(data)  # 将数据传入回测系统

    # 设置资产
    cerebro.broker.setcash(200000.0)
    # 设置佣金
    cerebro.broker.setcommission(commission=0.00015)
    # 添加回测策略，设置自定义参数数值
    cerebro.addstrategy(TestStrategy)
    # 执行策略
    cerebro.run()
    # 画图
    cerebro.plot()
