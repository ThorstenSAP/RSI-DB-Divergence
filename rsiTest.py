import datetime
from typing import Callable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pandas_datareader.data as web
import yfinance as yf
import yahoo_fin.stock_info as si

import xlsxwriter


nasdaqTickersAdj = []
nasdaqTickerErrors = []
nasdaq = si.tickers_nasdaq()
cnt = 0
amntTickers = len(nasdaq)

for ticker in nasdaq:
    print(ticker, "start prozessing ticker", cnt, " of ", amntTickers)
    try:
        netIncome = si.get_cash_flow(ticker, yearly = True)
        netIncomeLastYear = netIncome.iloc[6] if netIncome.empty == False else [0]
        if netIncomeLastYear[0] > 1000000.0:
            nasdaqTickersAdj.append(ticker)
    except:
        nasdaqTickerErrors.append(ticker)
        print(ticker, "error occured")
    
    cnt = cnt + 1

print(nasdaqTickersAdj)
print(nasdaqTickerErrors)