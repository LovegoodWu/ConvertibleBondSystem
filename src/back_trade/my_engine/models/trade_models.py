class TradeRecord:
    def __init__(self, date, bond_code, price, quantity, is_buy):
        self.date = date  # 交易日期
        self.bond_code = bond_code  # 债券代码
        self.price = price  # 交易价格
        self.quantity = quantity  # 交易数量
        self.is_buy = is_buy  # 交易类型，True表示买入，False表示卖出


class Position:
    def __init__(self, bond_code):
        self.bond_code = bond_code  # 债券代码
        self.quantity = 0  # 持仓数量
        self.cost_basis = 0.0  # 平均买入成本
        self.current_value = 0.0  # 当前市值
        self.current_profit = 0.0  # 当前收益

    def update_position(self, trade):
        if trade.is_buy:
            self.quantity += trade.quantity
            self.cost_basis = (self.cost_basis * (
                    self.quantity - trade.quantity) + trade.price * trade.quantity) / self.quantity
        else:
            self.quantity -= trade.quantity
            if self.quantity < 0:
                raise ValueError("卖出数量超过持仓数量")
        self.current_value = self.quantity * trade.price
        self.current_profit = self.current_value - self.quantity * self.cost_basis
