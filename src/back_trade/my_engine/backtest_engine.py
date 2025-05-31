import pandas as pd

from src.back_trade.my_engine.models.trade_models import Position, TradeRecord


class BacktestEngine:
    def __init__(self, data, strategy, start_time, end_time, frequency='D', initial_funds=100000):
        self.data = data  # 历史行情数据，格式为 MultiIndex (date, bond_code)
        self.strategy = strategy  # 回测策略
        self.start_time = start_time
        self.end_time = end_time
        self.frequency = frequency  # 策略运行频率
        self.initial_funds = initial_funds  # 初始资金
        self.current_funds = initial_funds  # 当前资金
        self.positions = {}  # 持仓情况 {bond_code: Position}
        self.trade_records = []  # 交易记录

    def run(self):
        # 根据开示结束时间，筛选出策略运行所需要的数据
        self.data = self.data[(self.data.index.get_level_values('date') >= self.start_time) &
                              (self.data.index.get_level_values('date') <= self.end_time)]

        # 根据频率筛选数据
        self.data['trade_date'] = self.data.index.get_level_values('date')
        if self.frequency == 'D':
            dates = self.data.index.get_level_values('date').unique()
        elif self.frequency == 'W':
            # 按照周分组，获取每一组内每一列最大值所在的索引
            last_trading_days = self.data.groupby(pd.Grouper(freq='W', level='date')).idxmax()
            # loc用索引定位数据行，index获取索引，get_level_values获取指复合索引中的某一个维度
            dates = self.data.loc[last_trading_days['trade_date']].index.get_level_values('date')
        elif self.frequency == 'M':
            last_trading_days = self.data.groupby(pd.Grouper(freq='M', level='date')).idxmax()
            dates = self.data.loc[last_trading_days['trade_date']].index.get_level_values('date')
        elif self.frequency == 'Q':
            last_trading_days = self.data.groupby(pd.Grouper(freq='Q', level='date')).idxmax()
            dates = self.data.loc[last_trading_days['trade_date']].index.get_level_values('date')
        elif self.frequency == 'Y':
            last_trading_days = self.data.groupby(pd.Grouper(freq='Y', level='date')).idxmax()
            dates = self.data.loc[last_trading_days['trade_date']].index.get_level_values('date')
        else:
            raise ValueError("Unsupported frequency")

        for date in dates:
            # 获取当日行情数据
            daily_data = self.data.xs(date, level='date')
            # 运行策略
            actions = self.strategy(daily_data, self.positions)
            # 执行交易
            for bond_code, action in actions.items():
                self.execute_trade(date, bond_code, action['price'], action['quantity'], action['action'] == 'buy')

    def execute_trade(self, date, bond_code, price, quantity, is_buy):
        if bond_code not in self.positions:
            self.positions[bond_code] = Position(bond_code)
        position = self.positions[bond_code]
        trade = TradeRecord(date, bond_code, price, quantity, is_buy)
        position.update_position(trade)
        self.trade_records.append(trade)
        if is_buy:
            self.current_funds -= price * quantity
        else:
            self.current_funds += price * quantity

    def get_performance(self):
        total_value = self.current_funds
        for position in self.positions.values():
            total_value += position.current_value
        return total_value, self.initial_funds, total_value - self.initial_funds

    def get_trade_records(self):
        return self.trade_records

    def get_positions(self):
        return self.positions
