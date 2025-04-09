# main.py
import pandas as pd

from backtest_engine import BacktestEngine
from constants.file_path import HISTORY_FILE_PATH
from strategies import simple_strategy
from utils.data_loader import load_data

if __name__ == "__main__":
    # 加载数据
    data = load_data(HISTORY_FILE_PATH)

    # 初始化回测引擎
    start_time = pd.to_datetime("2018-01-01")
    end_time = pd.to_datetime("2024-12-31")
    engine = BacktestEngine(data, simple_strategy, start_time, end_time, frequency='M', initial_funds=100000)

    # 运行回测
    engine.run()

    # 获取回测结果
    total_value, initial_funds, profit = engine.get_performance()
    print(f"初始资金: {initial_funds}")
    print(f"最终资产: {total_value}")
    print(f"总收益: {profit}")

    # 获取交易记录
    trade_records = engine.get_trade_records()
    for record in trade_records:
        print(f"日期: {record.date}, 价格: {record.price}, 数量: {record.quantity}, 买入: {record.is_buy}")

    # 获取持仓情况
    positions = engine.get_positions()
    for bond_code, position in positions.items():
        print(
            f"债券代码: {bond_code}, 持仓数量: {position.quantity}, 当前市值: {position.current_value}, 当前收益: {position.current_profit}")

    # 保存交易记录和持仓情况
    # engine.save_results('results/backtest_results.csv')
