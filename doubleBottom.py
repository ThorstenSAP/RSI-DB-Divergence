import yfinance as yf
import yahoo_fin.stock_info as si
from typing import Callable
import numpy as np
import pandas as pd


#._values holds the data in an array with the following format 
# [Open, High, Low, Close, Volume, Dividends, Splits]
closeIndex = 3
lowIndex = 2

rsiLength = 14
daysAheadThreshold = 2



#._values will have the latest data on top (at index 0)
#print(res._values[0][3])
#Date is store here
#res.index.date[64]


#Stolen from: https://stackoverflow.com/questions/20526414/relative-strength-index-in-python-pandas
# Define function to calculate the RSI
def calc_rsi(over: pd.Series, fn_roll: Callable) -> pd.Series:
    # Get the difference in price from previous step
    delta = over.diff()
    # Get rid of the first row, which is NaN since it did not have a previous row to calculate the differences
    #delta = delta[1:] 

    # Make the positive gains (up) and negative gains (down) Series
    up, down = delta.clip(lower=0), delta.clip(upper=0).abs()

    roll_up, roll_down = fn_roll(up), fn_roll(down)
    rs = roll_up / roll_down
    rsi = 100.0 - (100.0 / (1.0 + rs))

    # Avoid division-by-zero if `roll_down` is zero
    # This prevents inf and/or nan values.
    rsi[:] = np.select([roll_down == 0, roll_up == 0, True], [100, 0, rsi])
    rsi.name = 'rsi'

    # Assert range
    valid_rsi = rsi[rsiLength - 1:]
    assert ((0 <= valid_rsi) & (valid_rsi <= 100)).all()
    # Note: rsi[:length - 1] is excluded from above assertion because it is NaN for SMA.

    return rsi



def getDoubleBottoms(yfResponse):
    aPotentailLows = [] #keeps track of the indices of the potential lows
    aLows = [] # the actual lows
    aDoubleBottoms = [] 

    #set index to the last possible day
    amntData = len(yfResponse._values) - 2 #Two candles are considered
    index = 0
    while index < amntData: 
        # searched the next two candles no lower low

        #criteria 2: it closes lower during the next two days
            # if true kick it
        bLowerLow = False
        daysAhead = 1
        while daysAhead <= 2:
            if(yfResponse._values[index + daysAhead][closeIndex] < yfResponse._values[index][closeIndex]):
                bLowerLow = True
                break

            if daysAhead == daysAheadThreshold and bLowerLow == False:
                aPotentailLows.append(index) if index not in aPotentailLows else aPotentailLows

            daysAhead = daysAhead + 1
            #elif (res._values[indexAhead][lowIndex] < res._values[indexAhead][lowIndex]):
        #else -> criteria 1: there is a new low
            #sub-criteria 1: it is more than 1% lower
                # kick it
            # save date

        #do something
        index = index + 1

    #ensure that each potentail low is checked against its past. Hence, it is not an potentail low if it had a lower low the two days before
    for potentialLowIndex in aPotentailLows:
        daysBackThreshold = 2
        daysBack = 1
        bLowerLow = False
        while daysBack <= daysBackThreshold:

            if(yfResponse._values[potentialLowIndex - daysBack][closeIndex] < yfResponse._values[potentialLowIndex][closeIndex]):
                bLowerLow = True
                break

            if daysBack == daysAheadThreshold and bLowerLow == False:
                aLows.append(potentialLowIndex) if potentialLowIndex not in aLows else aLows

            daysBack = daysBack + 1        


    #first loop goes until the second last entry
    #second loop is always one entry ahead of the first one. Hence, it goes until the last entry
    amntLows = len(aLows)
    firstIndex = 0
    secondIndex = 0

    while firstIndex < amntLows - 2:
        secondIndex = firstIndex + 1 # second index is at least one step ahead of first index
        firstLowIndex = aLows[firstIndex] # ensure to get the index of the actual low
        
        while secondIndex < amntLows - 1:
            secondLowIndex = aLows[secondIndex]
            if (0.985 < yfResponse._values[firstLowIndex][closeIndex] / yfResponse._values[secondLowIndex][closeIndex] and yfResponse._values[firstLowIndex][closeIndex] / yfResponse._values[secondLowIndex][closeIndex] < 1.015):
                #print ("DB: ", yfResponse.index.date[firstLowIndex], " - ", yfResponse.index.date[secondLowIndex])
                #DONT divide by 0.0
                if (yfResponse.rsi._values[secondLowIndex] != 0 and yfResponse.rsi._values[firstLowIndex] != 0):
                    if (yfResponse.rsi._values[secondLowIndex] / yfResponse.rsi._values[firstLowIndex] > 1.2):
                        #ensure that one first bottom will not occur more than 3 times
                        cnt = 0
                        aDoubleBottoms.append(firstLowIndex)
                        for doublebottomFirstIndex in aDoubleBottoms:
                            if doublebottomFirstIndex == firstLowIndex:
                                cnt = cnt +1
                        
                        if cnt <= 3:
                            # TODO check if date of secondLowIndex is within the past 5 days
                            #aDoubleBottoms.append(firstLowIndex)
                            print("RSI Divergence + DB: ", yfResponse.index.date[firstLowIndex], " - ", yfResponse.index.date[secondLowIndex])
            
            secondIndex = secondIndex +1
        
        firstIndex = firstIndex + 1 


dow = si.tickers_dow()
#dow = ['AAPL', 'DOW', 'DIS']
for ticker in dow:
    print(ticker)
    stock = yf.Ticker(ticker)
    res = stock.history("3mo", "1d")
    res.rsi = calc_rsi(res['Close'], lambda s: s.ewm(alpha=1 / rsiLength).mean())
    getDoubleBottoms(res)

# http://theautomatic.net/yahoo_fin-documentation/
# Loop with each ticker over the script
#print (si.tickers_dow())
#print (si.tickers_sp500())
#print (si.tickers_nasdaq())
#tickers_dow
#tickers_ftse100
#tickers_ftse250
#tickers_ibovespa
#tickers_nasdaq
#tickers_nifty50
#tickers_niftybank
#tickers_other
#tickers_sp500