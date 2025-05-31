from src.back_trade.my_engine.models.trade_models import Position


def simple_strategy(daily_data, positions):
    actions = {}
    for bond_code, row in daily_data.iterrows():
        price = row['close']
        if price <= 110:
            actions[bond_code] = {'action': 'buy', 'price': price, 'quantity': 10}
        elif bond_code in positions and positions.get(bond_code).quantity >= 10 and price > 130:
            actions[bond_code] = {'action': 'sell', 'price': price, 'quantity': 10}
    return actions
