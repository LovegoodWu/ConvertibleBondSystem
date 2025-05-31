# utils/performance.py
import numpy as np


def calculate_performance(returns):
    annual_return = np.mean(returns) * 252
    max_drawdown = np.min(returns)
    sharpe_ratio = annual_return / np.std(returns)
    return annual_return, max_drawdown, sharpe_ratio
