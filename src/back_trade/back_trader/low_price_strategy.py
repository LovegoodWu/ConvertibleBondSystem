import time
from datetime import datetime

import backtrader as bt
import pandas as pd

from constants.file_path import HISTORY_FILE_PATH, HISTORY_MOCK_FILE_PATH
from src.back_trade.back_trader.pandas_data_convertible_bond import PandasDataConvertibleBond


def downcast(amount, lot):
    return abs(amount // lot * lot)


class LowPriceConvertibleBondStrategy(bt.Strategy):
    params = (
        ('num_bonds', 20),
        ('interval_days', 10),
        ('bond_code_to_name_dict', {}),
    )

    def __init__(self):
        print("--------- 打印 self.datas 第一个数据表格的 lines ----------")
        print(self.data0.lines.getlinealiases())
        print("num_bonds:", self.p.num_bonds)
        print("name_to_code_dict:", self.p.bond_code_to_name_dict)

        self.order = None
        self.hold_list = []

    def prenext(self):
        self.next()

    def next(self):
        today = self.datetime.date(0)

        # 每隔 interval_days 天执行一次策略
        if (len(self) - 1) % self.p.interval_days != 0:
            return

        # 获取所有可转债的收盘价
        bond_data_dict = {}
        for data in self.datas:
            bond_code_str = data._name
            bond_date = data.datetime.date(0)

            # 股票还未上市，跳过
            if today != bond_date:
                continue

            # len(data)是已经处理过的bar的个数，包含当前bar
            # 股票明天就要退市了
            if len(data) + 1 >= data.buflen():
                continue

            bond_data_dict[bond_code_str] = data

        # 按收盘价排序，选取最低的 num_bonds 个可转债
        sorted_bonds = sorted(bond_data_dict.items(), key=lambda x: (x[1].close[0] + x[1].stock_premium_rate[0]))
        selected_bonds = [code for code, _ in sorted_bonds[:self.p.num_bonds]]

        hold_set = set(self.hold_list)
        should_buy_set = set(selected_bonds)

        need_sell_list = list(hold_set - should_buy_set)
        need_sell_list.sort()
        for code in need_sell_list:
            data = self.getdatabyname(code)
            self.order = self.order_target_percent(data, 0, name=code)
            # self.log(f"卖{code}, price:{data.close[0]:.3f}, double_low: {data.close[0] + data.stock_premium_rate[0]:.3f}, pct: 0")
            self.hold_list.remove(code)

        need_buy_list = list(should_buy_set - hold_set)
        need_buy_list.sort()
        for code in need_buy_list:
            data = self.getdatabyname(code)
            order_value = self.broker.getvalue() * (1 / self.p.num_bonds)
            order_amount = downcast(order_value / data.close[0], 10)
            self.order = self.buy(data, size=order_amount, name=code)
            # self.log(f"买{code}, price:{data.close[0]:.3f}, double_low: {data.close[0] + data.stock_premium_rate[0]:.3f}, amount: {order_amount}")
            self.hold_list.append(code)

        self.hold_list.sort()
        self.log(
            f'资产：{self.broker.getvalue():.2f} 持仓：{[(x, self.p.bond_code_to_name_dict[x], self.getpositionbyname(x).size) for x in self.hold_list]}')

    # def notify_order(self, order):
    #     if order.status in [order.Submitted, order.Accepted]:
    #         return
    #
    #     if order.status in [order.Completed, order.Canceled, order.Margin]:
    #         if order.isbuy():
    #             self.log(f"""买入{order.info['name']}, 成交量{order.executed.size}，成交价{order.executed.price:.2f}""")
    #             self.log(
    #                 f'资产：{self.broker.getvalue():.2f} 持仓：{[(x, self.getpositionbyname(x).size) for x in self.hold_list]}')
    #         elif order.issell():
    #             self.log(f"""卖出{order.info['name']}, 成交量{order.executed.size}，成交价{order.executed.price:.2f}""")
    #             self.log(
    #                 f'资产：{self.broker.getvalue():.2f} 持仓：{[(x, self.getpositionbyname(x).size) for x in self.hold_list]}')

    def log(self, txt, dt=None):
        dt = dt or self.datetime.date(0)
        print('%s , %s' % (dt.isoformat(), txt))


if __name__ == '__main__':
    start_time = time.time()

    cerebro = bt.Cerebro(stdstats=False, optdatas=True)

    data_csv = pd.read_csv(HISTORY_FILE_PATH, encoding='GBK')
    data_csv = data_csv.dropna()
    data_csv = data_csv[~data_csv['credit_level'].str.contains('B|C', na=False)]

    data_csv['date'] = pd.to_datetime(data_csv['date'])
    data_csv['close'] = pd.to_numeric(data_csv['close'])
    data_csv['open'] = pd.to_numeric(data_csv['close'])
    data_csv['low'] = pd.to_numeric(data_csv['close'])
    data_csv['high'] = pd.to_numeric(data_csv['close'])
    data_csv['volume'] = 0
    data_csv['stock_premium_rate'] = pd.to_numeric(data_csv['stock_premium_rate'])

    start_date = datetime(2021, 1, 4)  # 回测开始时间
    end_date = datetime(2024, 12, 31)  # 回测结束时间
    data_csv = data_csv[(data_csv['date'] >= start_date) & (data_csv['date'] <= end_date)]

    # 根据data_csv生成一个dict，dict的key是data_csv中的bond_code列，value是对应的bond_name的值
    bond_code_to_name_dict = {str(code): name for code, name in zip(data_csv['bond_code'], data_csv['bond_name'])}

    cerebro.addstrategy(LowPriceConvertibleBondStrategy, num_bonds=20, interval_days=1,
                        bond_code_to_name_dict=bond_code_to_name_dict)

    # 按债券代码分组
    grouped = data_csv.groupby('bond_code')

    # 为每个债券代码创建数据馈送
    for bond_code, group in grouped:
        # 将 date 列转换为 datetime 类型并设置为索引
        group['date'] = pd.to_datetime(group['date'])
        group = group.set_index('date')
        group = group.sort_index()

        # if i == 0:
        #     target_index = group.index
        # else:
        #     group = group.reindex(target_index).ffill()
        #     group = group.dropna()

        data_feed = PandasDataConvertibleBond(
            dataname=group,
            fromdate=start_date,
            todate=end_date,
            open='open',
            high='high',
            low='low',
            close='close',
            volume='volume',  # 必须有这一列，否则会报错
            openinterest=-1,
            # premium_rate='premium_rate',
            # credit_level='credit_level'
        )
        # 数据名必须是str
        cerebro.adddata(data_feed, name=str(bond_code))

    end_time = time.time()
    print("加载数据耗时：", end_time - start_time, "秒")

    cerebro.broker.setcash(1000000.0)
    cerebro.broker.setcommission(commission=0.001)

    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
    start_time = time.time()

    # 运行回测
    cerebro.run()
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

    end_time = time.time()
    print("回测运行耗时：", end_time - start_time, "秒")

    # 绘制图表
    # cerebro.plot()
