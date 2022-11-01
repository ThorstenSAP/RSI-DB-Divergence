from pickle import TRUE
import yfinance as yf
import yahoo_fin.stock_info as si
from typing import Callable
import numpy as np
import pandas as pd
import xlsxwriter
import datetime
from datetime import datetime


#._values holds the data in an array with the following format 
# [Open, High, Low, Close, Volume, Dividends, Splits]
closeIndex = 3
lowIndex = 2

rsiLength = 14
daysAheadThreshold = 2



def writeHeaderInExcel(worksheet):
    worksheet.write('A1', 'Ticker')
    worksheet.write('B1', 'Date1')
    worksheet.write('C1', 'Date2')


def resultToExcel(oResult, worksheet, row):
    writeHeaderInExcel(worksheet)

    #For-Schleife über die Namen
    for firstIndex, secondIndex in oResult['result']:
        worksheet.write('A'+str(row), oResult['ticker'])
        worksheet.write('B'+str(row), oResult['data'].index.date[firstIndex].strftime('%d.%m.%Y')) #.strftime('%x') in order that the xlsx file will accept the format
        worksheet.write('C'+str(row), oResult['data'].index.date[secondIndex].strftime('%d.%m.%Y'))
        #incrementieren der Zeilennummer
        row = row + 1

def daysBetween(d1, d2):
    #d1 = datetime.strptime(d1, "%Y-%m-%d")
    #d2 = datetime.strptime(d2, "%Y-%m-%d")
    return abs((d2 - d1).days)

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



def getDoubleBottoms(yfResponse, ticker, worksheet, worksheetRow):
    aPotentailLows = [] #keeps track of the indices of the potential lows
    aLows = [] # the actual lows
    aDoubleBottoms = [] 
    oRes = {'ticker': ticker,
            'result': [],
            'data':yfResponse}

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
            if(yfResponse._values[index + daysAhead][closeIndex] > yfResponse._values[index][closeIndex]):
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

            if(yfResponse._values[potentialLowIndex - daysBack][closeIndex] > yfResponse._values[potentialLowIndex][closeIndex]):
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
                            # check if date of secondLowIndex is within the past 5 days. Since, the date is used make the threshold of days to 7
                            if(daysBetween(yfResponse.index.date[secondLowIndex], datetime.today().date()) < 7):
                                oRes['result'].append([firstLowIndex, secondLowIndex])
                                print("RSI Divergence + DB: ", yfResponse.index.date[firstLowIndex], " - ", yfResponse.index.date[secondLowIndex])
            
            secondIndex = secondIndex +1
        
        firstIndex = firstIndex + 1

    # prefill an Excel file
    resultToExcel(oRes, worksheet, worksheetRow)
    #return the updated row. Hence, it will kept updating
    return worksheetRow + len(oRes['result'])


# Create XLSX for output
workbook = xlsxwriter.Workbook('DoubleTop.xlsx')
worksheet = workbook.add_worksheet('Tabellenname')
worksheetRow = 2 # start to fill data in row 2


dow = si.tickers_dow()
sp500 = si.tickers_sp500()
#nasdaq = si.tickers_nasdaq() - gefilter auf jährlicher netIncome > 1.Mio
nasdaqTickersAdj1 = ['AADI', 'AAL', 'AAME', 'AAON', 'AAPL', 'AATC', 'AAWW', 'ABCB', 'ABCL', 'ABCM', 'ABIO', 'ABMD', 'ABNB', 'ABSI', 'ABVC', 'ACGL', 'ACGLN', 'ACGLO', 'ACHC', 'ACHL', 'ACHV', 'ACIU', 'ACIW', 'ACLS', 'ACMR', 'ACNT', 'ACQR', 'ACRS', 'ACRX', 'ACVA', 'ADAP', 'ADBE', 'ADEA', 'ADER', 'ADES', 'ADI', 'ADIL', 'ADP', 'ADSK', 'ADTH', 'ADUS', 'ADVM', 'ADXN', 'AEAC', 'AEAE', 'AEHA', 'AEHR', 'AEI', 'AEIS', 'AEMD', 'AEP', 'AERC', 'AESE', 'AFAC', 'AFBI', 'AFCG', 'AFRM', 'AFYA', 'AGEN', 'AGFY', 'AGGR', 'AGIO', 'AGLE', 'AGMH', 'AGNC', 'AGNCM', 'AGNCN', 'AGNCO', 'AGNCP', 'AGTC', 'AHCO', 'AHI', 'AHRN', 'AIMC', 'AIRS', 'AIRT', 'AIRTP', 'AKAM', 'AKIC', 'AKTS', 'ALDX', 'ALGM', 'ALGN', 'ALGS', 'ALGT', 'ALKS', 'ALNY', 'ALOR', 'ALOT', 'ALPN', 'ALPP', 'ALRM', 'ALRS', 'ALTO', 'AMAL', 'AMAT', 'AMCX', 'AMD', 'AMED', 'AMEH', 'AMGN', 'AMKR', 'AMPG', 'AMPH', 'AMPL', 'AMRK', 'AMRN', 'AMSF', 'AMST', 'AMSWA', 'AMTB', 'AMTI', 'AMZN', 'ANDE', 'ANEB', 'ANGO', 'ANIK', 'ANSS', 'ANY', 'AOGO', 'AOSL', 'APA', 'APEI', 'APLT', 'APM', 'APOG', 'APP', 'APPF', 'APPS', 'APXI', 'AQB', 'AQMS', 'ARAY', 'ARBE', 'ARBK', 'ARCB', 'ARCC', 'ARDX', 'AREC', 'ARGU', 'ARGX', 'ARHS', 'ARKO', 'ARKOW', 'ARKR', 'ARLP', 'AROW', 'ARQT', 'ARRW', 'ARRY', 'ARTL', 'ARTNA', 'ARVL', 'ASLE', 'ASML', 'ASND', 'ASO', 'ASPS', 'ASTL', 'ASYS', 'ATAI', 'ATAX', 'ATEC', 'ATLC', 'ATLCP', 'ATLO', 'ATNF', 'ATNX', 'ATOS', 'ATRC', 'ATRI', 'ATSG', 'ATVI', 'ATY', 'AUB', 'AUBAP', 'AUBN', 'AUDC', 'AUR', 'AURA', 'AUTL', 'AVAC', 'AVAV', 'AVCO', 'AVGO', 'AVID', 'AVNW', 'AVPT', 'AXDX', 'AXGN', 'AXLA', 'AXTI', 'AZN', 'AZTA', 'BAFN', 'BANF', 'BANR', 'BAOS', 'BASE', 'BBCP', 'BBGI', 'BBIG', 'BBIO', 'BBLG', 'BBSI', 'BCAB', 'BCEL', 'BCML', 'BCOR', 'BCOV', 'BCOW', 'BCPC', 'BCRX', 'BCTX', 'BEAM', 'BEAT', 'BECN', 'BFIN', 'BFRI', 'BFST', 'BGCP', 'BGFV', 'BGNE', 'BGRY', 'BHAC', 'BIDU', 'BIGC', 'BIIB', 'BILI', 'BIMI', 'BIOL', 'BIOS', 'BITF', 'BIVI', 'BKNG', 'BKSC', 'BL', 'BLBX', 'BLDE', 'BLDP', 'BLFY', 'BLKB', 'BLMN', 'BLNG', 'BLRX', 'BLU', 'BMBL', 'BMEA', 'BMRN', 'BNGO', 'BNIX', 'BNOX', 'BNSO', 'BNTX', 'BOCN', 'BOKF', 'BON', 'BOOM', 'BOTJ', 'BPOP', 'BPRN', 'BPTH', 'BPTS', 'BPYPN', 'BPYPO', 'BPYPP', 'BRIV', 'BRKH', 'BRKL', 'BRKR', 'BRLT', 'BROG', 'BRP', 'BSBK', 'BSET', 'BSKY', 'BSQR', 'BSVN', 'BSY', 'BTAI', 'BTBT', 'BTMD', 'BTRS', 'BUSE', 'BVS', 'BWAY', 'BWC', 'BWEN', 'BWMX', 'BYFC', 'BYND', 'BYRN', 'BYTS', 'BZFD', 'CAAS', 'CAC', 'CACC', 'CADL', 'CAKE', 'CALM', 'CAN', 'CAPR', 'CARE', 'CARV', 'CASA', 'CASH', 'CASY', 'CATC', 'CATY', 'CBAN', 'CBAT', 'CBAY', 'CBRG', 'CBSH', 'CCAP', 'CCB', 'CCBG', 'CCEP', 'CCLP', 'CCNC', 'CCNE', 'CCNEP', 'CCOI', 'CCSI', 'CD', 'CDMO', 'CDNA', 'CDNS', 'CDRO', 'CDW', 'CDZI', 'CDZIP', 'CELH', 'CELZ', 'CENN', 'CENT', 'CENTA', 'CERS', 'CFFI', 'CFLT', 'CFSB', 'CG', 'CGC', 'CGNX', 'CGO', 'CHCI', 'CHDN', 'CHI', 'CHK', 'CHKP', 'CHNR', 'CHRD', 'CHRS', 'CHRW', 'CHSCL', 'CHSCM', 'CHSCN', 'CHSCO', 'CHSCP', 'CHTR', 'CHUY', 'CHX', 'CHY', 'CIDM', 'CIFR', 'CINF', 'CIVB', 'CIZN', 'CLAR', 'CLBK', 'CLBT', 'CLFD', 'CLLS', 'CLMT', 'CLNE', 'CLOV', 'CLPS', 'CLPT', 'CLRM', 'CLRO', 'CLSK', 'CLST', 'CLWT', 'CLXT', 'CMBM', 'CMCA', 'CMCO', 'CMCSA', 'CME', 'CMPO', 'CMPS', 'CNEY', 'CNSL', 'CNTB', 'CNTX', 'CNTY', 'CNXC', 'COCO', 'CODA', 'CODX', 'COHU', 'COIN', 'COKE', 'COLB', 'COLI', 'COLL', 'COLM', 'CONN', 'COOP', 'CORT', 'CORZ', 'COST', 'COUP', 'COVA', 'COWN', 'CPAA', 'CPAR', 'CPRT', 'CPRX', 'CPSH', 'CPSS', 'CRAI', 'CRBP', 'CRBU', 'CRCT', 'CREC', 'CREG', 'CRESY', 'CRNC', 'CROX', 'CRSP', 'CRSR', 'CRTO', 'CRUS', 'CRZN', 'CSBR', 'CSCO', 'CSGP', 'CSGS', 'CSII', 'CSIQ', 'CSQ', 'CSSE', 'CSSEP', 'CSTE', 'CSWC', 'CSWI', 'CSX', 'CTAS', 'CTG', 'CTHR', 'CTIC', 'CTKB', 'CTRM', 'CTSH', 'CUEN', 'CULL', 'CUTR', 'CVBF', 'CVCO', 'CVLG', 'CVLY', 'CVT', 'CVV', 'CWBC', 'CWBR', 'CWST', 'CYAD', 'CYBE', 'CYCC', 'CYCCP', 'CYRX', 'CYT', 'CYTO', 'CYXT', 'CZFS', 'CZR', 'DADA', 'DALS', 'DAOO', 'DARE', 'DAVE', 'DAWN', 'DBTX', 'DBX', 'DCGO', 'DCOM', 'DCOMP', 'DDI', 'DFFN', 'DGICA', 'DGICB', 'DGII', 'DGLY', 'DGNU', 'DHC', 'DHCA', 'DHHC', 'DHIL', 'DIBS', 'DICE', 'DIOD', 'DISH', 'DJCO', 'DKDCA', 'DKNG', 'DLCA', 'DLHC', 'DLO', 'DLTH', 'DLTR', 'DMAC', 'DMLP', 'DMTK', 'DNUT', 'DOCU', 'DOGZ', 'DOOO', 'DORM', 'DOX', 'DPRO', 'DRCT', 'DRIO', 'DRMA', 'DRRX', 'DRTT', 'DRVN', 'DSGX', 'DSKE', 'DSP', 'DSWL', 'DUOL', 'DVAX', 'DXCM', 'DXLG', 'DYNT', 'EA', 'EAC', 'EBAC', 'EBAY', 'EBC', 'EBET', 'EBIX', 'EBMT', 'EBON', 'ECBK', 'EDAP', 'EDRY', 'EDUC', 'EEFT', 'EEIQ', 'EFSC', 'EFSCP', 'EFTR', 'EGAN', 'EGLE', 'EGLX', 'EHTH', 'EJH', 'EKSO', 'ELBM', 'ELTK', 'EM', 'EMBC', 'EMCF', 'EMKR', 'EML', 'ENPH', 'ENSC', 'ENSG', 'ENTG', 'ENTX', 'ENTXW', 'ENVB', 'ENVX', 'EOLS', 'EOSE', 'EPHY', 'EPIX', 'EQBK', 'EQIX', 'ERIC', 'ERIE', 'ERII', 'ERYP', 'ESAC', 'ESCA', 'ESEA', 'ESGR', 'ESGRO', 'ESGRP', 'ESSA', 'ETNB', 'ETSY', 'EVGN', 'EVO', 'EVOJ', 'EVOP', 'EVTV', 'EWBC', 'EWCZ', 'EXAI', 'EXAS', 'EXC', 'EXEL', 'EXPD', 'EXPE', 'EXPI', 'EXPO', 'EYE', 'EYPT', 'EZFL', 'EZGO', 'FA', 'FAMI', 'FANG', 'FANH', 'FAST', 'FBMS', 'FBNC', 'FCFS', 'FCNCA', 'FCNCO', 'FCNCP', 'FDUS', 'FEIM', 'FELE', 'FFBW', 'FFHL', 'FFIC', 'FFIN', 'FFIV', 'FFWM', 'FGBI', 'FGBIP', 'FGEN', 'FHLT', 'FHTX', 'FIAC', 'FICV', 'FINM', 'FINW', 'FISI', 'FISV', 'FITB', 'FITBI', 'FITBO', 'FITBP', 'FIVE', 'FIVN', 'FIZZ', 'FKWL', 'FLEX', 'FLGC', 'FLGT', 'FLL', 'FLWS', 'FMAO', 'FMBH', 'FMIV', 'FMNB', 'FNHC', 'FNKO', 'FNVT', 'FNWB', 'FNWD', 'FOCS', 'FOLD', 'FONR', 'FORA', 'FORM', 'FORR', 'FORTY', 'FOX', 'FOXA', 'FPAY', 'FRAF', 'FRBN', 'FRG', 'FRGAP', 'FRHC', 'FRME', 'FRMEP', 'FRON', 'FRPT', 'FRST', 'FRW', 'FSBC', 'FSBW', 'FSEA', 'FSLR', 'FSRX', 'FSTR', 'FSV', 'FTAI', 'FTAIN', 'FTAIO', 'FTAIP', 'FTCI', 'FTEK', 'FTFT', 'FTNT', 'FTVI', 'FULC', 'FULT', 'FULTP', 'FUSB', 'FUTU', 'FVCB', 'FWRD', 'FXNC', 'FYBR', 'GABC', 'GAIA', 'GAIN', 'GALT', 'GAMB', 'GAMC', 'GBNY', 'GDEN', 'GDEV', 'GDS', 'GDST', 'GDYN', 'GEEX', 'GEG', 'GERN', 'GEVO', 'GFGD', 'GFS', 'GGAL', 'GGMC', 'GH', 'GHRS', 'GIII', 'GILD', 'GIPR', 'GIW', 'GLBS', 'GLHA', 'GLLI', 'GLNG', 'GLPG', 'GLPI', 'GLUE', 'GMAB', 'GNAC', 'GNFT', 'GNPX', 'GNTX', 'GNTY', 'GNUS', 'GOEVW', 'GOGL', 'GOOD', 'GOODN', 'GOODO', 'GOOG', 'GOOGL', 'GPAC', 'GPP', 'GPRE', 'GPRO', 'GRAB', 'GRCL', 'GRFS', 'GRIN', 'GROW', 'GRPH', 'GRPN', 'GRTS', 'GRTX', 'GRVY', 'GRWG', 'GSBC', 'GSHD', 'GSMG', 'GT', 'GTAC', 'GTBP', 'GTEC', 'GTH', 'GTHX', 'GTIM', 'GURE', 'GWAV', 'GWII', 'GWRS', 'GXII', 'HA', 'HAFC', 'HAIA', 'HAIN', 'HALL', 'HALO', 'HAS', 'HBAN', 'HBANM', 'HBANP', 'HBNC', 'HBT', 'HCCI', 'HCIC', 'HCII', 'HCM', 'HCP', 'HCSG', 'HCVI', 'HDSN', 'HEES', 'HELE', 'HEPS', 'HERA', 'HEXO', 'HFWA', 'HGEN', 'HHR', 'HIBB', 'HIII', 'HIMX', 'HITI', 'HIVE', 'HLAH', 'HLIT', 'HLNE', 'HLTH', 'HMNF', 'HMPT', 'HNNA', 'HNST', 'HOFT', 'HOLI', 'HOLX', 'HON', 'HOOD', 'HOPE', 'HOUR', 'HOWL', 'HPK', 'HPLT', 'HQI', 'HQY', 'HRMY', 'HRTX', 'HSDT', 'HSIC', 'HST', 'HSTM', 'HTBK', 'HTGM', 'HTLF', 'HTLFP', 'HTZ', 'HUBG', 'HUDI', 'HUMA', 'HURC', 'HURN', 'HWBK', 'HWC', 'HWKN', 'HYFM', 'HYW', 'HZNP', 'IAC', 'IART', 'IBEX', 'IBKR', 'IBOC', 'IBRX', 'IBTX', 'ICCC', 'ICCH', 'ICFI', 'ICHR', 'ICLR', 'ICMB', 'ICUI', 'ICVX', 'IDCC', 'IDEX', 'IDRA', 'IDXX', 'IEP', 'IFBD', 'IFRX', 'IGIC', 'IIIV', 'IIVIP', 'IKNA', 'IKT', 'ILMN', 'ILPT', 'IMCC', 'IMKTA', 'IMMR', 'IMOS', 'IMVT', 'IMXI', 'INBK', 'INCR', 'INCY', 'INDB', 'INDP', 'INDT', 'INM', 'INMD', 'INSM', 'INTC', 'INTG', 'INTU', 'INVA', 'INVE', 'INVO', 'INVZ', 'IOAC', 'IOBT', 'IONM', 'IONR', 'IONS', 'IOSP', 'IOVA', 'IPAR', 'IPDN', 'IPGP', 'IPWR', 'IQ', 'IRBT', 'IRDM', 'IREN', 'IRIX', 'IRMD', 'IROQ', 'IRTC', 'IRWD', 'ISPO', 'ISRG', 'ISUN', 'ITIC', 'ITOS', 'ITQ', 'ITRM', 'ITRN', 'IVAC', 'IVCB', 'IXHL', 'JACK', 'JAQC', 'JAZZ', 'JCIC', 'JD', 'JFIN', 'JG', 'JJSF', 'JKHY', 'JMAC', 'JOAN', 'JOFF', 'JRSH', 'JSPR', 'JUGG', 'JVA', 'JWAC', 'JWEL', 'JYNT', 'KAII', 'KAIR', 'KALA', 'KARO', 'KBAL', 'KDP', 'KE', 'KELYA', 'KELYB', 'KEQU', 'KFFB', 'KFRC', 'KHC', 'KIII', 'KINS', 'KLAQ', 'KLIC', 'KMPH', 'KNDI', 'KOSS', 'KPLT', 'KRNL', 'KRON', 'KRT', 'KTCC', 'KTRA', 'KTTA', 'KURA', 'KVHI', 'KXIN', 'KYMR', 'KZR', 'LAMR', 'LAND', 'LANDM', 'LANDO']
nasdaqTickersAdj2 = ['PGC', 'PGEN', 'PGNY', 'PGRW', 'PHAR', 'PHIO', 'PHVS', 'PI', 'PINC', 'PIRS', 'PLAB', 'PLAY', 'PLL', 'PLMR', 'PLPC', 'PLSE', 'PLTK', 'PLUG', 'PLUS', 'PMCB', 'PMGM', 'PNBK', 'PNFP', 'PNFPP', 'PNRG', 'PNTG', 'PODD', 'POET', 'POOL', 'POW', 'POWI', 'POWW', 'POWWP', 'PPBI', 'PPBT', 'PPIH', 'PPTA', 'PRAA', 'PRCH', 'PRCT', 'PRDO', 'PRFT', 'PRGS', 'PRIM', 'PRPH', 'PRPL', 'PRTA', 'PRTG', 'PRTH', 'PRTK', 'PSAG', 'PSEC', 'PSNL', 'PTC', 'PTCT', 'PTLO', 'PTNR', 'PTON', 'PTPI', 'PTRA', 'PTSI', 'PUBM', 'PULM', 'PVBC', 'PWOD', 'PWP', 'PXLW', 'PYPL', 'PYR', 'PZZA', 'QCOM', 'QDEL', 'QFIN', 'QH', 'QIWI', 'QLI', 'QLYS', 'QNST', 'QRHC', 'QRTEA', 'QRTEB', 'QRTEP', 'QRVO', 'QSI', 'QUMU', 'QURE', 'RADA', 'RAVE', 'RBB', 'RCAT', 'RCII', 'RCKY', 'RCM', 'RCMT', 'RDFN', 'RDHL', 'RDI', 'RDIB', 'RDVT', 'RDWR', 'REAL', 'REAX', 'REFI', 'REG', 'REGN', 'REKR', 'RELL', 'REPL', 'REVH', 'RGCO', 'RGEN', 'RGLD', 'RGNX', 'RGP', 'RICK', 'RILY', 'RILYL', 'RILYP', 'RKDA', 'RMBS', 'RMGC', 'RMNI', 'RNAZ', 'RNST', 'RNW', 'RNWK', 'ROCC', 'ROCK', 'ROIC', 'ROIV', 'ROKU', 'ROOT', 'ROST', 'ROVR', 'RPAY', 'RPD', 'RPID', 'RPRX', 'RRBI', 'RRGB', 'RRR', 'RSSS', 'RSVR', 'RUSHA', 'RUSHB', 'RWLK', 'RXRX', 'RXST', 'RYAAY', 'RZLT', 'SAFT', 'SAIA', 'SALM', 'SAMA', 'SAMG', 'SANM', 'SASI', 'SASR', 'SATS', 'SAVA', 'SBAC', 'SBCF', 'SBFG', 'SBLK', 'SBNY', 'SBNYP', 'SBT', 'SBTX', 'SBUX', 'SCAQ', 'SCHL', 'SCHN', 'SCKT', 'SCSC', 'SCVL', 'SDAC', 'SEDG', 'SEEL', 'SEIC', 'SELF', 'SERA', 'SESN', 'SFBC', 'SFE', 'SFET', 'SFM', 'SFNC', 'SFST', 'SGBX', 'SGC', 'SGH', 'SGHT', 'SGII', 'SGRY', 'SHAC', 'SHC', 'SHCA', 'SHIP', 'SHLS', 'SHOO', 'SHYF', 'SIBN', 'SIEB', 'SIER', 'SIFY', 'SIGI', 'SIGIP', 'SILC', 'SILO', 'SIMO', 'SIRI', 'SITM', 'SIVB', 'SIVBP', 'SJ', 'SKYA', 'SKYW', 'SLAB', 'SLAM', 'SLGC', 'SLGG', 'SLGL', 'SLM', 'SLMBP', 'SLN', 'SLP', 'SLRX', 'SMBC', 'SMCI', 'SMID', 'SMLR', 'SMMT', 'SMPL', 'SMTC', 'SNAX', 'SNBR', 'SNCE', 'SNCY', 'SNDL', 'SNDX', 'SNEX', 'SNFCA', 'SNPS', 'SNPX', 'SNSE', 'SNT', 'SNTI', 'SNY', 'SOFI', 'SOHU', 'SONO', 'SOPH', 'SOTK', 'SOVO', 'SP', 'SPFI', 'SPKB', 'SPLK', 'SPNE', 'SPNS', 'SPSC', 'SPTK', 'SPWR', 'SQFT', 'SQFTP', 'SQL', 'SRAD', 'SRCL', 'SRDX', 'SRGA', 'SRNE', 'SRRK', 'SSB', 'SSBK', 'SSNC', 'SSP', 'SSRM', 'SSSS', 'STAA', 'STAF', 'STBA', 'STEP', 'STGW', 'STIM', 'STKS', 'STRA', 'STRL', 'STRR', 'STRRP', 'STRS', 'STSA', 'STX', 'SUPN', 'SURF', 'SVA', 'SVFA', 'SVNA', 'SVVC', 'SWBI', 'SWET', 'SWIM', 'SWKH', 'SWKS', 'SYBT', 'SYBX', 'SYM', 'SYNA', 'SYNH', 'SYRS', 'TA', 'TACT', 'TAIT', 'TALK', 'TARS', 'TAYD', 'TBBK','TBPH', 'TCBC', 'TCBI', 'TCBIO', 'TCBS', 'TCBX', 'TCDA', 'TCOM', 'TCON', 'TCRX', 'TCX', 'TDUP', 'TEAM', 'TECH', 'TECTP', 'TEDU', 'TENB', 'TER', 'TERN', 'TFSL', 'TGAA', 'TGTX', 'TH', 'THFF', 'THRM', 'THRN', 'THRY', 'THTX', 'TIGO', 'TIGR', 'TIOA', 'TIPT', 'TITN', 'TIVC', 'TKLF', 'TKNO', 'TLGY', 'TLIS', 'TMC', 'TMKR', 'TNDM', 'TNXP', 'TOAC', 'TOI', 'TOPS', 'TOWN', 'TPG', 'TRDA', 'TREE', 'TRIN', 'TRIP', 'TRMB', 'TRMK', 'TRMR', 'TRNS', 'TRON', 'TRS', 'TRVG', 'TSAT', 'TSBK', 'TSCO', 'TSLA', 'TSVT', 'TTD', 'TTEC', 'TTEK', 'TTMI', 'TTWO', 'TUEM', 'TW', 'TWIN', 'TWLV', 'TWNK', 'TWOU', 'TWST', 'TXN', 'TXRH', 'TZPS', 'UAL', 'UBCP', 'UBSI', 'UBX', 'UCL', 'UCTT', 'UEIC', 'UFCS', 'UFPI', 'UFPT', 'UGRO', 'UHAL', 'UK', 'ULH', 'ULTA', 'UMBF', 'UNAM', 'UNIT', 'UONE', 'UONEK', 'UPC', 'UPST', 'UPWK', 'URBN', 'UROY', 'USAU', 'USCB', 'USCT', 'USEG', 'USLM', 'UTHR', 'UTMD', 'UTME', 'UVSP', 'VACC', 'VALU', 'VBFC', 'VBIV', 'VBLT', 'VBNK', 'VBTX', 'VC', 'VCSA', 'VCTR', 'VECO', 'VEDU', 'VEEE', 'VELO', 'VEON', 'VERU', 'VFF', 'VHNA', 'VIA', 'VIASP', 'VIAV', 'VICR', 'VINC', 'VINO', 'VINP', 'VIR', 'VIRT', 'VITL', 'VIVE', 'VIVK', 'VIVO', 'VJET', 'VLGEA', 'VLNS', 'VLON', 'VLY', 'VLYPO', 'VLYPP', 'VMAR', 'VNDA', 'VNOM', 'VOD', 'VORB', 'VRA', 'VRAY', 'VRCA', 'VREX', 'VRME', 'VRNT', 'VRPX', 'VRRM', 'VRSK', 'VRSN', 'VRTS', 'VRTX', 'VSAC', 'VSEC', 'VTIQ', 'VTRU', 'VTVT', 'VTYX', 'VUZI', 'VWE', 'VYNE', 'WABC', 'WAFU', 'WASH', 'WAVD', 'WB', 'WBA', 'WBD', 'WDAY', 'WDC', 'WDFC', 'WEN', 'WERN', 'WEYS', 'WFCF', 'WHF', 'WHLM', 'WIMI', 'WINA', 'WIRE', 'WLFC', 'WMG', 'WOOF', 'WPRT', 'WRAP', 'WRLD', 'WSBF', 'WSC', 'WSFS', 'WTBA', 'WTFC', 'WTFCM', 'WTFCP', 'WTMA', 'WTW', 'WULF', 'WW', 'WWD', 'XCUR', 'XEL', 'XFIN', 'XFOR', 'XMTR', 'XNCR', 'XNET', 'XOMA', 'XOMAO', 'XOMAP', 'XOS', 'XP', 'XPAX', 'XRAY', 'XRTX', 'XXII', 'YI', 'YJ', 'YMAB', 'YMTX', 'YNDX', 'YTRA', 'YVR', 'Z', 'ZBRA', 'ZD', 'ZENV', 'ZEUS', 'ZG', 'ZI', 'ZIMV', 'ZION', 'ZIONO', 'ZIONP', 'ZKIN', 'ZM', 'ZT', 'ZUMZ', 'ZWRK', 'ZYNE']


#other = si.tickers_other()
#dow = ['AAPL', 'DOW', 'DIS']
indizes = [dow, sp500, nasdaqTickersAdj1, nasdaqTickersAdj2]
for index in indizes:
    for ticker in index:
        print(ticker)
        stock = yf.Ticker(ticker)
        res = stock.history("3mo", "1d")
        res.rsi = calc_rsi(res['Close'], lambda s: s.ewm(alpha=1 / rsiLength).mean())
        worksheetRow = getDoubleBottoms(res, ticker, worksheet, worksheetRow)

workbook.close()

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


#one to one copy against the doubleBottom script. Adjusted the if statements about the lower low in line 92 and 116