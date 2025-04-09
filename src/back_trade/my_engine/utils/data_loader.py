# utils/data_loader.py
import pandas as pd


def load_data(file_path):
    return pd.read_csv(file_path, index_col=['date', 'bond_code'], parse_dates=True, encoding='GBK')
