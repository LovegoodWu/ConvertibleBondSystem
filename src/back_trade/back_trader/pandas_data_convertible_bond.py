import backtrader as bt


class PandasDataConvertibleBond(bt.feeds.PandasData):
    lines = ('stock_premium_rate',)  # 要添加的线
    # 设置 line 在数据源上的列位置
    params = (
        ('stock_premium_rate', -1),
    )
