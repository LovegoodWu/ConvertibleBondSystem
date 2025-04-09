import os
from os.path import abspath, dirname

PROJECT_ROOT_PATH = dirname(dirname(abspath(__file__)))
HISTORY_FILE_DIRECTORY = os.path.join(PROJECT_ROOT_PATH, "data/history")
HISTORY_FILE_PATH = os.path.join(HISTORY_FILE_DIRECTORY, "history_akshare.csv")
HISTORY_MOCK_FILE_PATH = os.path.join(HISTORY_FILE_DIRECTORY, "history_akshare_mock.csv")
